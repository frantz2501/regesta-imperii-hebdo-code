#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Moteur de moissonnage du fond RI OPAC -> spool/page_NNNNNN.jsonl.

Le serveur OAI-PMH encode ses resumptionTokens sous la forme
"{cursor};oai_dc;;;" : chaque page est adressable directement, ce qui
permet un spool par page avec reprise sans perte. L'etat d'avancement
partag' avec flush.py vit dans state.json :

  - pages present dans spool/  = moissonnees, pas encore purgees
  - next_page_needed / last_page_flushed = progression du flush
  - total_pages  = ceil(completeListSize / 100), mesure au bootstrap

Reprise : on repart de next_page_needed (pages deja flushees) ; les
pages restants dans le spool sont ecartees par le test d'existence.
"""

import datetime as dt
import json
import os
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ri_opac_api as ri

BASE = os.path.dirname(os.path.abspath(__file__))
SPOOL = os.path.join(BASE, "spool")
STATE_FILE = os.path.join(BASE, "state.json")
DISK_GUARD_BYTES = 2_000_000_000  # pause si le spool depasse 2 Go (push en echec)
WORKERS = 6
DELAY = 0.3            # politesse par worker
TIMEOUT = 180          # le serveur ralentit sous charge ; etre tolerant
MAX_ATTEMPTS = 15
OAI_NS = ri.OAI_NS


def log(msg):
    print(f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}",
          flush=True)


def page_path(n):
    return os.path.join(SPOOL, f"page_{n:06d}.jsonl")


def spool_pages():
    out = []
    for name in os.listdir(SPOOL) if os.path.isdir(SPOOL) else []:
        if re.fullmatch(r"page_\d+\.jsonl", name):
            out.append(int(name[5:11]))
    return sorted(out)


def spool_size():
    total = 0
    for name in os.listdir(SPOOL) if os.path.isdir(SPOOL) else []:
        try:
            total += os.path.getsize(os.path.join(SPOOL, name))
        except OSError:
            pass
    return total


def read_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def write_state(**updates):
    state = read_state()
    state.update(updates)
    state["updated"] = dt.datetime.now().isoformat(timespec="seconds")
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)


class Coordinator:
    """Distribution des pages aux workers, arret sur derniere page."""

    def __init__(self, total=None):
        self.lock = threading.Lock()
        self.next = 1
        self.total = total
        self.hard_stop = False

    def claim(self):
        with self.lock:
            if self.hard_stop:
                return None
            if self.total is not None and self.next > self.total:
                return None
            page = self.next
            self.next += 1
            return page

    def set_total(self, total):
        with self.lock:
            if self.total is None and total and total >= 1:
                self.total = total
                log(f"total : {total} pages")

    def abort(self):
        with self.lock:
            self.hard_stop = True


def parse_container(container):
    records = [client._parse_record(el)
               if False else None for el in []]  # placeholder
    raise NotImplementedError


def fetch_page(client, n):
    """Retourne (records, next_token_existe, complete_list_size)."""
    body = client._request(verb="ListRecords",
                           resumptionToken=f"{n};oai_dc;;;")
    root = ET.fromstring(body)
    container = root.find(f"{{{OAI_NS}}}ListRecords")
    if container is None:
        return [], False, 0
    records = []
    for el in container.findall(f"{{{OAI_NS}}}record"):
        records.append(client._parse_record(el))
    token_el = container.find(f"{{{OAI_NS}}}resumptionToken")
    has_next = bool((token_el.text or "").strip()) if token_el is not None else False
    try:
        complete = int(token_el.get("completeListSize") or 0)
    except (AttributeError, TypeError, ValueError):
        complete = 0
    return records, has_next, complete


def save_page(n, records):
    tmp = page_path(n) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.replace(tmp, page_path(n))


def bootstrap(client):
    """Premiere requete (sans token) : elle seule porte completeListSize.

    Retourne (records_page1, complete_list_size).
    """
    body = client._request(verb="ListRecords", metadataPrefix="oai_dc")
    root = ET.fromstring(body)
    container = root.find(f"{{{OAI_NS}}}ListRecords")
    records, complete = [], 0
    if container is not None:
        for el in container.findall(f"{{{OAI_NS}}}record"):
            records.append(client._parse_record(el))
        token_el = container.find(f"{{{OAI_NS}}}resumptionToken")
        try:
            complete = int(token_el.get("completeListSize") or 0)
        except (AttributeError, TypeError, ValueError):
            complete = 0
    return records, complete


def worker(coord, _wid):
    client = ri.RIOpacClient(delay=DELAY, timeout=TIMEOUT,
                             user_agent="ri-opac-oaipmh-vps-harvest/1.0")
    session_records = 0
    while True:
        page = coord.claim()
        if page is None:
            write_state(records_session=session_records)
            return
        if os.path.exists(page_path(page)):
            continue  # deja moissonnee (reprise)
        while spool_size() > DISK_GUARD_BYTES:
            log(f"page {page}: spool > garde-fou 2 Go, pause 120 s")
            time.sleep(120)
        attempts = 0
        while True:
            try:
                records, has_next, complete = fetch_page(client, page)
                save_page(page, records)
                session_records += len(records)
                if not has_next and records:
                    log(f"page {page} sans resumptionToken : fin du fond")
                    coord.set_total(page)
                spooled = len(spool_pages())
                state = read_state()
                flushed = state.get("last_page_flushed", 0)
                total = coord.total or state.get("total_pages")
                done = min(flushed + spooled,
                           total if total else flushed + spooled)
                log(f"page {page} ok ({len(records)}) ; "
                    + (f"{done}/{total} ({100 * done / total:.1f}%)"
                       if total else f"{done} pages")
                    + f", spool={spooled}")
                write_state(total_pages=coord.total,
                            records_session=session_records)
                break
            except ri.OAIPMHError as exc:
                if exc.code == "noRecordsMatch":
                    log(f"page {page}: fin du depot (noRecordsMatch)")
                    coord.set_total(page - 1)
                    break
                slow = exc.code in ("badResumptionToken", "idDoesNotExist")
                wait = 60 if slow else min(300, 15 * 2 ** attempts)
                log(f"page {page}: erreur OAI {exc.code}, essai {attempts + 1} "
                    f"dans {wait} s")
                attempts += 1
                if attempts >= MAX_ATTEMPTS:
                    coord.abort()
                    return
                time.sleep(wait)
            except Exception as exc:  # reseau, XML, ...
                attempts += 1
                if attempts >= MAX_ATTEMPTS:
                    log(f"ERREUR page {page} apres {attempts} essais : "
                        f"{exc!r} ; arret (le superviseur relancera)")
                    coord.abort()
                    return
                wait = min(300, 15 * 2 ** attempts)
                log(f"page {page}: echec ({exc!r}), nouvel essai dans "
                    f"{wait} s [{attempts}]")
                time.sleep(wait)


def main():
    os.makedirs(SPOOL, exist_ok=True)
    state = read_state()
    total = state.get("total_pages")
    coord = Coordinator(total=total)

    # page de reprise : jamais en dessous de ce que le flush a deja pousse
    start = state.get("next_page_needed") or 1
    with coord.lock:
        coord.next = max(1, int(start))

    spooled = spool_pages()
    log(f"demarrage : page {coord.next}, spool={len(spooled)} pages, "
        f"total={'connu: ' + str(coord.total) if coord.total else 'inconnu'}")

    if coord.total is None:
        client = ri.RIOpacClient(delay=DELAY, timeout=TIMEOUT,
                                 user_agent="ri-opac-oaipmh-vps-harvest/1.0")
        for attempt in range(MAX_ATTEMPTS):
            try:
                records, complete = bootstrap(client)
                if complete:
                    coord.set_total(max(1, -(-complete // max(len(records), 1))))
                    write_state(total_pages=coord.total)
                if (coord.next == 1 and
                        not os.path.exists(page_path(1))):
                    save_page(1, records)
                    with coord.lock:
                        coord.next = 2
                log(f"bootstrap ok ({len(records)} notices page 1, "
                    f"completeListSize={complete})")
                break
            except Exception as exc:
                wait = min(300, 15 * 2 ** attempt)
                log(f"bootstrap echoue ({exc!r}), nouvel essai dans {wait} s")
                time.sleep(wait)
        else:
            log("bootstrap impossible ; arret (le superviseur relancera)")
            return

    write_state(harvest_pid=os.getpid(),
                started=dt.datetime.now().isoformat(timespec="seconds"))
    threads = [threading.Thread(target=worker, args=(coord, i), daemon=True)
               for i in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if coord.total is not None:
        state = read_state()
        spooled = spool_pages()
        last = max(state.get("last_page_flushed", 0), max(spooled or [0]))
        if last >= coord.total:
            with open(os.path.join(BASE, "HARVEST.done"), "w") as fh:
                fh.write(dt.datetime.now().isoformat(timespec="seconds") + "\n")
            log(f"MOISSONNAGE TERMINE : {coord.total} pages")
        else:
            log(f"toutes les pages connues traitrees mais il manque "
                f"des pages < {last} ({coord.total}) ; relance necessaire")
    else:
        log("arret avant la fin ; le superviseur relancera")


if __name__ == "__main__":
    main()
