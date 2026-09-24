#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client OAI-PMH pour le RI OPAC (Regesta Imperii OPAC).

Interface : https://opac.regesta-imperii.de/api/oai (protocole OAI-PMH 2.0)

Verbs : Identify, ListSets, ListMetadataFormats, GetRecord, ListRecords,
ListIdentifiers. Formats : oai_dc, oai_marc, bibtex (GetRecord uniquement).

Cas d'usage "digest" :
    python ri_opac_api.py latest --since 2026-07-01
    python ri_opac_api.py latest --since 2026-07-01 --language ger --query "Karl"
    python ri_opac_api.py latest --last 50 --language fre,ita
    python ri_opac_api.py latest --since 2026-07-01 --markdown rapport.md

Moissonnage brut avec les memes filtres cote client (equivalent de
latest --since, mais sans le tri par recence) :
    python ri_opac_api.py list-records --from 2026-03-01 --language fre --markdown fre.md

Moissonnage parallele (le serveur accepte les curseurs arbitraires de ses
resumptionTokens ; debit plafonne a ~2x cote serveur) :
    python ri_opac_api.py --delay 0.3 list-records --workers 6 --from 2026-01-01 --jsonl brut.jsonl

Filtres disponibles (appliques cote client, l'API OAI-PMH ne sachant pas
filtrer par langue ni faire de recherche plein texte) :
  --language   : codes ISO 639-2 du champ dc:language (ger, fre, ita, ...)
  --query      : recherche insensible a la casse dans le titre (dc:title),
                 les mots-cles (dc:subject) et les auteurs (dc:creator) ;
                 plusieurs mots = ET logique
  --set        : filtre cote serveur sur un setSpec (EuropaeischeGeschichte, ...)
  --published-after : filtre sur l'annee de publication (dc:date)

Notes conformes a la doc officielle (OPAC_OAIPMH_API_DOC) :
  - le depot declare deletedRecord=transient : des headers status="deleted"
    (sans metadonnees) peuvent apparaitre ; le digest les ignore ;
  - la doc cite "oai_bib" et des exemples ListRecords avec metadataPrefix=bibtex :
    en pratique le serveur declare "bibtex" et le refuse sur List* (erreur
    cannotDisseminateFormat) ; bibtex reste donc reserve a GetRecord ;
  - granularite des dates : YYYY-MM-DD (UTC), pas de dimension horaire.

Stdlib uniquement, aucune dependance.
"""

import argparse
import datetime as dt
import json
import queue
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE_URL = "https://opac.regesta-imperii.de/api/oai"
OAI_NS = "http://www.openarchives.org/OAI/2.0/"
DC_PREFIXES = ("oai_dc", "oai_marc", "bibtex")
LIST_PREFIXES = ("oai_dc", "oai_marc")
PAGE_SIZE = 100  # taille de page serveur (constatee empiriquement)


class OAIPMHError(Exception):
    """Erreur retournee par le serveur dans un element <error code="...">."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message.strip()}")


class RIOpacClient:
    def __init__(self, base_url=BASE_URL, delay=1.0, timeout=60,
                 user_agent="ri-opac-oaipmh-client/1.1"):
        self.base_url = base_url
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent
        self._last_request_time = 0.0

    # ------------------------------------------------------------------ HTTP

    def _request(self, **params):
        """Effectue une requete OAI-PMH et retourne le corps brut (bytes).

        Leve OAIPMHError si la reponse XML contient un element <error>.
        """
        self._polite_wait()
        url = self.base_url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()
        self._last_request_time = time.monotonic()

        # GetRecord+metadataPrefix=bibtex renvoie du BibTeX brut, pas du XML.
        if params.get("verb") == "GetRecord" and params.get("metadataPrefix") == "bibtex":
            if not body.lstrip().startswith(b"<?xml"):
                return body
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return body
        error = root.find(f"{{{OAI_NS}}}error")
        if error is not None:
            raise OAIPMHError(error.get("code"), error.text or "")
        return body

    def _polite_wait(self):
        elapsed = time.monotonic() - self._last_request_time
        if self.delay and self._last_request_time and elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    # ----------------------------------------------------------------- verbs

    def identify(self):
        root = ET.fromstring(self._request(verb="Identify"))
        identify = root.find(f"{{{OAI_NS}}}Identify")
        return {child.tag.split("}")[1]: (child.text or "").strip()
                for child in identify}

    def list_sets(self):
        root = ET.fromstring(self._request(verb="ListSets"))
        out = []
        for container in root.iter(f"{{{OAI_NS}}}set"):
            entry = {child.tag.split("}")[1]: (child.text or "").strip()
                     for child in container}
            out.append(entry)
        return out

    def list_metadata_formats(self, identifier=None):
        params = {"verb": "ListMetadataFormats"}
        if identifier is not None:
            params["identifier"] = identifier
        root = ET.fromstring(self._request(**params))
        out = []
        for fmt in root.iter(f"{{{OAI_NS}}}metadataFormat"):
            entry = {child.tag.split("}")[1]: (child.text or "").strip()
                     for child in fmt}
            out.append(entry)
        return out

    def get_record(self, identifier, prefix="oai_dc"):
        """Retourne un dict : header + metadonnees parsees.

        prefix="bibtex" -> la cle "bibtex" contient le BibTeX brut.
        """
        body = self._request(verb="GetRecord", metadataPrefix=prefix,
                             identifier=identifier)
        if not body.lstrip().startswith(b"<?xml"):
            return {"identifier": str(identifier),
                    "bibtex": body.decode("utf-8", errors="replace").strip()}
        root = ET.fromstring(body)
        record = root.find(f".//{{{OAI_NS}}}record")
        return self._parse_record(record)

    def list_records(self, prefix="oai_dc", from_=None, until=None, set_=None,
                     limit=None, max_pages=None, workers=1):
        """Generateur de records (dicts), suit les resumptionTokens.

        workers > 1 : les pages sont recuperees en parallele par des workers
        (curseurs adressables), l'ordre de sortie reste celui du serveur.
        """
        if workers and workers > 1:
            return self._list_parallel("ListRecords", prefix, from_, until,
                                       set_, limit, max_pages,
                                       with_metadata=True, workers=workers)
        return self._list("ListRecords", prefix, from_, until, set_, limit,
                          max_pages, with_metadata=True)

    def list_identifiers(self, prefix="oai_dc", from_=None, until=None,
                         set_=None, limit=None, max_pages=None, workers=1):
        """Generateur de headers (dicts), suit les resumptionTokens.

        workers > 1 : cf. list_records.
        """
        if workers and workers > 1:
            return self._list_parallel("ListIdentifiers", prefix, from_, until,
                                       set_, limit, max_pages,
                                       with_metadata=False, workers=workers)
        return self._list("ListIdentifiers", prefix, from_, until, set_, limit,
                          max_pages, with_metadata=False)

    def _list(self, verb, prefix, from_, until, set_, limit, max_pages,
              with_metadata, resume_token=None):
        if prefix not in LIST_PREFIXES:
            raise ValueError(
                f"{verb} accepte uniquement {LIST_PREFIXES} "
                f"(recu: {prefix}) ; bibtex ne fonctionne que pour GetRecord")
        if resume_token:
            params = {"verb": verb, "resumptionToken": resume_token}
        else:
            params = {"verb": verb, "metadataPrefix": prefix}
            if from_:
                params["from"] = from_
            if until:
                params["until"] = until
            if set_:
                params["set"] = set_

        count = 0
        page = 0
        while True:
            try:
                root = ET.fromstring(self._request(**params))
            except OAIPMHError as exc:
                if exc.code == "noRecordsMatch":
                    return
                raise
            container = root.find(f"{{{OAI_NS}}}{verb}")
            if container is None:
                return
            for element in container.findall(f"{{{OAI_NS}}}record" if with_metadata
                                             else f"{{{OAI_NS}}}header"):
                if with_metadata:
                    yield self._parse_record(element)
                else:
                    yield self._parse_header(element)
                count += 1
                if limit is not None and count >= limit:
                    return
            page += 1
            if max_pages is not None and page >= max_pages:
                return
            token_el = container.find(f"{{{OAI_NS}}}resumptionToken")
            token = (token_el.text or "").strip() if token_el is not None else ""
            if not token:
                return
            params = {"verb": verb, "resumptionToken": token}

    def _list_parallel(self, verb, prefix, from_, until, set_, limit, max_pages,
                       with_metadata, workers):
        """Variante multi-threads de _list (cf. --workers).

        Le serveur encode ses resumptionTokens sous la forme
        "{cursor};{prefix};{from};{until};{set}" et accepte un curseur
        arbitraire : chaque page est adressable directement, ce qui permet
        a plusieurs workers de moissone le courant en parallele. Les
        enregistrements sortent dans l'ordre du serveur (identifiant
        croissant), exactement comme en sequentiel.

        Precaution (deletedRecord=transient) : une suppression pendant le
        moissonnage decale les pages ; les doublons d'identifiant adjacents
        sont ecartes, mais une notice decalee de plus d'une page peut
        manquer — re-moissonner la fenetre en cas de doute.
        """
        element_tag = (f"{{{OAI_NS}}}record" if with_metadata
                       else f"{{{OAI_NS}}}header")
        parse = self._parse_record if with_metadata else self._parse_header

        def parse_page(container):
            return [parse(el) for el in container.findall(element_tag)]

        params = {"verb": verb, "metadataPrefix": prefix}
        if from_:
            params["from"] = from_
        if until:
            params["until"] = until
        if set_:
            params["set"] = set_
        try:
            root = ET.fromstring(self._request(**params))
        except OAIPMHError as exc:
            if exc.code == "noRecordsMatch":
                return
            raise
        container = root.find(f"{{{OAI_NS}}}{verb}")
        if container is None:
            return
        first_page = parse_page(container)
        token_el = container.find(f"{{{OAI_NS}}}resumptionToken")
        next_token = (token_el.text or "").strip() if token_el is not None else ""
        if not next_token:
            yield from first_page
            return
        if ";" not in next_token:
            # token sans curseur pilote : on rend la premiere page puis on
            # poursuit sequentiellement a partir du token renvoye
            yield from first_page
            remaining_limit = (limit - len(first_page)
                                if limit is not None else None)
            remaining_pages = max_pages - 1 if max_pages is not None else None
            yield from self._list(verb, prefix, from_, until, set_,
                                  remaining_limit, remaining_pages,
                                  with_metadata, resume_token=next_token)
            return

        template = next_token.split(";", 1)[1]
        try:
            complete = int(token_el.get("completeListSize") or 0)
        except (TypeError, ValueError):
            complete = 0
        # le token non vide prouve que la page 2 existe ; completeListSize,
        # quand il est coherent, donne directement la derniere page
        page_len = max(len(first_page), 1)
        last_page = max(-(-complete // page_len) if complete else 1, 2)
        if max_pages is not None:
            last_page = min(last_page, max_pages)

        results = queue.Queue(maxsize=workers * 4)
        stop = threading.Event()
        cond = threading.Condition()
        progress = {"next": 2, "last": last_page, "inflight": 0}

        def claim():
            with cond:
                while True:
                    if stop.is_set():
                        return None
                    if progress["next"] <= progress["last"]:
                        page_no = progress["next"]
                        progress["next"] += 1
                        progress["inflight"] += 1
                        return page_no
                    if progress["inflight"] == 0:
                        return None  # plus de pages connues ni en cours
                    cond.wait(timeout=0.5)

        def deliver(item):
            while not stop.is_set():
                try:
                    results.put(item, timeout=0.5)
                    return True
                except queue.Empty:
                    continue
            return False

        def finish_page(page_no, has_next):
            with cond:
                if has_next and page_no + 1 > progress["last"]:
                    progress["last"] = page_no + 1
                    if max_pages is not None:
                        progress["last"] = min(progress["last"], max_pages)
                progress["inflight"] -= 1
                cond.notify_all()

        def abort(failure):
            stop.set()
            with cond:
                cond.notify_all()
            results.put((None, None, failure))  # sans condition d'arret

        def worker():
            wclient = RIOpacClient(base_url=self.base_url, delay=self.delay,
                                   timeout=self.timeout,
                                   user_agent=self.user_agent)
            try:
                while True:
                    page_no = claim()
                    if page_no is None:
                        break
                    try:
                        wroot = ET.fromstring(wclient._request(
                            verb=verb,
                            resumptionToken=f"{page_no};{template}"))
                        wcontainer = wroot.find(f"{{{OAI_NS}}}{verb}")
                        records = (parse_page(wcontainer)
                                   if wcontainer is not None else [])
                        wtoken_el = (wcontainer.find(
                                        f"{{{OAI_NS}}}resumptionToken")
                                    if wcontainer is not None else None)
                        has_next = (bool((wtoken_el.text or "").strip())
                                    if wtoken_el is not None else False)
                        failure = None
                    except OAIPMHError as exc:
                        if exc.code == "noRecordsMatch":
                            records, has_next, failure = [], False, None
                        else:
                            records, has_next, failure = None, False, exc
                    except Exception as exc:  # reseau, XML mal forme, ...
                        records, has_next, failure = None, False, exc
                    if failure is not None:
                        abort(failure)
                        return
                    if not deliver((page_no, records, None)):
                        return  # arrete par le consommateur (limit atteint)
                    finish_page(page_no, has_next)
                deliver((None, None, None))
            except Exception as exc:  # imprevu : ne pas bloquer le consommateur
                abort(exc)

        threads = [threading.Thread(target=worker, daemon=True)
                   for _ in range(workers)]
        for thread in threads:
            thread.start()

        buffer = {1: first_page}
        expected = 1
        finished = 0
        count = 0
        last_id = None
        try:
            while True:
                while expected in buffer:
                    for rec in buffer.pop(expected):
                        rid = rec.get("identifier")
                        if rid is not None and rid == last_id:
                            continue  # page decalee par une suppression
                        if rid is not None:
                            last_id = rid
                        count += 1
                        yield rec
                        if limit is not None and count >= limit:
                            return
                    expected += 1
                if finished == workers:
                    return
                page_no, records, failure = results.get()
                if failure is not None:
                    raise failure
                if page_no is None:
                    finished += 1
                    continue
                buffer[page_no] = records
        finally:
            stop.set()
            with cond:
                cond.notify_all()

    # -------------------------------------------------- cas d'usage "digest"

    def latest(self, since=None, last=None, prefix="oai_dc", set_=None,
               languages=None, query=None, published_after=None,
               limit=None, max_pages_per_day=50, lookback_days=730,
               _today=None):
        """Retourne (records, stats) pour un digest.

        - since="YYYY-MM-DD" : toutes les notices de datestamp >= since
        - last=N             : les N notices les plus recentes (par datestamp)

        languages : liste de codes dc:language acceptes (ex. ["ger", "fre"]).
        query     : recherche plein texte (titre + sujet + createur), ET logique.
        published_after : annee minimale extraite de dc:date.

        NB : "recent" = datestamp OAI (date d'ajout/modification dans l'OPAC),
        pas l'annee de publication de l'oeuvre. Les mises a jour massives
        (migrations) creent des jours a plusieurs dizaines de milliers de
        notices : dans ce cas --last N est un echantillon deterministe,
        limite par max_pages_per_day.
        """
        if (since is None) == (last is None):
            raise ValueError("indiquer soit --since, soit --last")
        if prefix not in LIST_PREFIXES:
            raise ValueError("les filtres et le digest exigent oai_dc ou oai_marc")
        filters_used = bool(languages or query or published_after is not None)
        if filters_used and prefix != "oai_dc":
            raise ValueError("--language/--query/--published-after exigent oai_dc")

        matcher = RecordMatcher(languages=languages, query=query,
                                published_after=published_after)
        records = []
        if since is not None:
            for rec in self.list_records(prefix=prefix, from_=since, set_=set_,
                                         limit=None):
                if rec.get("datestamp") and rec["datestamp"] < since:
                    continue
                if rec.get("status") == "deleted":
                    continue  # transient : header sans metadonnees
                if matcher.matches(rec):
                    records.append(rec)
                if limit is not None and len(records) >= limit:
                    break
        else:
            today = _today or dt.date.today()
            n_wanted = int(last)
            if limit is not None and limit < n_wanted:
                n_wanted = limit
            newest = self.max_datestamp(today=today, set_=set_)
            if newest is None:
                records = []
            else:
                day = newest
                max_day = day - dt.timedelta(days=lookback_days)
                while day >= max_day and len(records) < n_wanted:
                    day_str = day.isoformat()
                    for rec in self.list_records(
                            prefix=prefix, from_=day_str, until=day_str,
                            set_=set_, max_pages=max_pages_per_day):
                        if rec.get("status") == "deleted":
                            continue  # transient : header sans metadonnees
                        if rec.get("datestamp") == day_str and matcher.matches(rec):
                            records.append(rec)
                            if len(records) >= n_wanted:
                                break
                    day -= dt.timedelta(days=1)
                records.sort(key=lambda r: (r.get("datestamp") or "",
                                            int(r.get("identifier") or 0)),
                             reverse=True)
                records = records[:n_wanted]

        stats = {"count": len(records), "filters": matcher.describe(),
                 "since": since, "last": last, "set": set_}
        if records:
            stats["datestamp_min"] = min(r["datestamp"] for r in records
                                         if r.get("datestamp"))
            stats["datestamp_max"] = max(r["datestamp"] for r in records
                                        if r.get("datestamp"))
            if prefix == "oai_dc":
                stats["by_language"] = _count_by(records, "language")
                stats["by_type"] = _count_by(records, "type")
        return records, stats

    def _earliest_datestamp(self):
        """earliestDatestamp declare par Identify (repli : 1980-01-04).

        La valeur sert de borne basse a la dichotomie de max_datestamp.
        Tolerante : on ne casse pas si Identify echoue ou si la date est
        mal formee.
        """
        try:
            raw = self.identify().get("earliestDatestamp", "")
            return dt.date.fromisoformat(raw[:10])
        except (ValueError, KeyError, OAIPMHError, ET.ParseError):
            return dt.date(1980, 1, 4)

    def max_datestamp(self, today=None, set_=None):
        """Date du datestamp le plus recent du depot (recherche binaire).

        ListIdentifiers(from=D) repond noRecordsMatch ssi aucun enregistrement
        n'a un datestamp >= D : la propriete est monotone en D, ce qui permet
        une dichotomie (~15 requetes) au lieu d'un parcours jour par jour.
        Retourne None si le depot est vide.
        """
        earliest = self._earliest_datestamp()
        today = today or dt.date.today()

        def has_records(day):
            try:
                gen = self.list_identifiers(from_=day.isoformat(),
                                            set_=set_, limit=1)
                return next(gen, None) is not None
            except OAIPMHError as exc:
                if exc.code == "noRecordsMatch":
                    return False
                raise

        if has_records(today):
            return today
        if not has_records(earliest):
            return None  # depot vide (ou vide avant earliest)
        lo, hi = earliest, today  # has_records(lo) vrai, has_records(hi) faux
        while hi - lo > dt.timedelta(days=1):
            mid = lo + (hi - lo) // 2
            if has_records(mid):
                lo = mid
            else:
                hi = mid
        return lo

    # -------------------------------------------------------------- parsing

    @staticmethod
    def _parse_header(header):
        out = {"identifier": None, "datestamp": None,
               "sets": [], "status": header.get("status")}
        for child in header:
            name = child.tag.split("}")[1]
            if name == "setSpec":
                out["sets"].append((child.text or "").strip())
            elif name in ("identifier", "datestamp"):
                out[name] = (child.text or "").strip()
        return out

    def _parse_record(self, record):
        header = record.find(f"{{{OAI_NS}}}header")
        out = self._parse_header(header) if header is not None else {}
        metadata = record.find(f"{{{OAI_NS}}}metadata")
        if metadata is not None:
            out["metadata"] = self._parse_metadata(metadata)
        return out

    def _parse_metadata(self, metadata):
        container = next(iter(metadata), None)
        if container is None:
            return None
        localname = container.tag.split("}")[1]
        if localname == "dc":  # Dublin Core (oai_dc)
            fields = {}
            for child in container:
                name = child.tag.split("}")[1]
                text = (child.text or "").strip()
                if text:
                    fields.setdefault(name, []).append(text)
            return {"format": "oai_dc", "fields": fields}
        if localname == "record":  # MARC 21 XML (oai_marc)
            leader = None
            controlfields = {}
            fields = []
            for element in container.iter():
                name = element.tag.split("}")[1]
                if name == "leader":
                    leader = (element.text or "").strip()
                elif name == "controlfield":
                    controlfields[element.get("tag")] = (element.text or "").strip()
                elif name == "datafield":
                    subfields = {}
                    for sub in element:
                        code = sub.get("code")
                        if code:
                            subfields.setdefault(code, []).append((sub.text or "").strip())
                    fields.append({"tag": element.get("tag"),
                                   "subfields": subfields})
            return {"format": "oai_marc", "leader": leader,
                    "controlfields": controlfields, "datafields": fields}
        return {"format": localname,
                "raw": ET.tostring(container, encoding="unicode")}


# ----------------------------------------------------------------- filtres

def _fold(text):
    """Minuscule + suppression des diacritiques pour une recherche tolerante."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


class RecordMatcher:
    """Filtres cote client : langue, requete plein texte, annee de publication.

    Les recherches portent sur dc:title, dc:subject et dc:creator (l'OPAC
    n'expose pas de dc:description). insensible a la casse et aux accents.
    """

    SEARCH_FIELDS = ("title", "subject", "creator")

    def __init__(self, languages=None, query=None, published_after=None):
        self.languages = [lang.strip().lower() for lang in (languages or []) if lang]
        self.query = query.strip().lower() if query else None
        self.published_after = int(published_after) if published_after else None

    def _dc_values(self, record, name):
        fields = (record.get("metadata") or {}).get("fields") or {}
        return [v for v in fields.get(name, []) if v]

    def matches(self, record):
        if self.languages:
            langs = [v.lower() for v in self._dc_values(record, "language")]
            if not any(lang in langs for lang in self.languages):
                return False
        if self.query:
            haystack = _fold(" ".join(
                value for name in self.SEARCH_FIELDS
                for value in self._dc_values(record, name)))
            if not all(_fold(word) in haystack
                       for word in self.query.split() if word):
                return False
        if self.published_after is not None:
            years = [int(y) for value in self._dc_values(record, "date")
                     for y in re.findall(r"\d{4}", value)]
            if not years or max(years) < self.published_after:
                return False
        return True

    def describe(self):
        desc = {}
        if self.languages:
            desc["language"] = self.languages
        if self.query:
            desc["query"] = self.query
        if self.published_after is not None:
            desc["published_after"] = self.published_after
        return desc


def _count_by(records, field):
    counts = {}
    for rec in records:
        values = ((rec.get("metadata") or {}).get("fields") or {}).get(field, [])
        for value in values:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


# ------------------------------------------------------------- rapport MD

def markdown_report(records, stats, title=None, max_rows=200):
    """Genere un rapport markdown dans l'esprit du repo regesta-imperii-hebdo."""
    lines = [title or f"Synthese RI OPAC - {dt.date.today().isoformat()}",
             "",
             f"**Genere le :** {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"**Source :** {BASE_URL} (OAI-PMH, licence CC BY 4.0)"]
    criteria = []
    if stats.get("since"):
        criteria.append(f"depuis {stats['since']}")
    if stats.get("last"):
        criteria.append(f"{stats['last']} dernieres notices")
    if stats.get("set"):
        criteria.append(f"set {stats['set']}")
    for key, label in (("language", "langues"), ("query", "recherche")):
        if stats.get("filters", {}).get(key):
            criteria.append(f"{label} : {stats['filters'][key]}")
    if stats.get("filters", {}).get("published_after"):
        criteria.append(f"publiees apres {stats['filters']['published_after']}")
    lines.append(f"**Criteres :** {' | '.join(criteria) if criteria else 'aucun'}")
    lines += ["", "---", "", "## Resume", "",
              f"- **Notices retenues :** {stats['count']}"]
    if stats.get("datestamp_min") and stats.get("datestamp_max"):
        lines.append(f"- **Datestamps :** {stats['datestamp_min']} -> "
                     f"{stats['datestamp_max']}")
    for key, label in (("by_language", "Langues"), ("by_type", "Types")):
        if stats.get(key):
            top = ", ".join(f"{k} ({v})" for k, v in list(stats[key].items())[:10])
            lines.append(f"- **{label} :** {top}")
    lines += ["", "## Notices", ""]
    if not records:
        lines.append("_Aucune notice ne correspond aux criteres._")
        return "\n".join(lines)
    lines += ["| ID | Titre | Auteurs | Annee | Langue | Type | Permalink |",
              "| --- | --- | --- | --- | --- | --- | --- |"]

    def cell(text, width=80):
        text = (text or "").replace("|", "/").replace("\n", " ").strip()
        return text if len(text) <= width else text[:width - 3] + "..."

    for rec in records[:max_rows]:
        fields = (rec.get("metadata") or {}).get("fields") or {}
        lines.append("| " + " | ".join([
            rec.get("identifier") or "",
            cell("; ".join(fields.get("title", [])), 100),
            cell("; ".join(fields.get("creator", []))),
            cell("; ".join(fields.get("date", [])), 20),
            cell("; ".join(fields.get("language", [])), 20),
            cell("; ".join(fields.get("type", [])), 30),
            f"https://opac.regesta-imperii.de/id/{rec.get('identifier')}",
        ]) + " |")
    if len(records) > max_rows:
        lines.append("")
        lines.append(f"_{len(records) - max_rows} notices supplementaires "
                     f"non affichees._")
    return "\n".join(lines)


# ---------------------------------------------------------------------- CLI

def _print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="ri_opac_api.py",
        description=("Client OAI-PMH du RI OPAC (Regesta Imperii).\n"
                     "\n"
                     "Verbs OAI-PMH exposes en sous-commandes : Identify,\n"
                     "ListSets, ListMetadataFormats, GetRecord, ListRecords,\n"
                     "ListIdentifiers. Formats : oai_dc, oai_marc (List*)\n"
                     "et en plus bibtex (GetRecord uniquement)."),
        epilog=("Exemples :\n"
                "  %(prog)s identify\n"
                "  %(prog)s list-sets\n"
                "  %(prog)s get-record 524395 --prefix oai_dc\n"
                "  %(prog)s get-record 524395 --prefix bibtex\n"
                "  %(prog)s list-records --from 2026-06-01 --until 2026-06-30 \\\n"
                "      --jsonl sortie.jsonl\n"
                "  %(prog)s list-records --from 2026-03-01 --language fre \\\n"
                "      --markdown fre.md\n"
                "  %(prog)s --delay 0.3 list-records --workers 6 \\\n"
                "      --from 2026-01-01 --jsonl brut.jsonl\n"
                "  %(prog)s latest --since 2026-06-24 --language fre \\\n"
                "      --markdown rapport.md\n"
                "  %(prog)s latest --last 50 --language fre,ita --query Karl\n"
                "\n"
                "Les filtres (--language, --query, --published-after) sont\n"
                "appliques cote client : l'API OAI-PMH ne sait pas filtrer\n"
                "par langue ni faire de recherche plein texte."),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=BASE_URL,
                        help="URL de l'endpoint OAI-PMH "
                             "(defaut : %(default)s)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="pause en secondes entre requetes HTTP, par "
                             "politesse envers le serveur (defaut : %(default)s)")
    sub = parser.add_subparsers(dest="command", required=True,
                                title="sous-commandes",
                                metavar="COMMANDE")

    def add_harvest_args(p):
        p.add_argument("--prefix", default="oai_dc", choices=LIST_PREFIXES,
                       help="format de metadonnees (defaut : %(default)s) ; "
                            "bibtex n'est accepte que par get-record")
        p.add_argument("--from", dest="from_", metavar="YYYY-MM-DD",
                       help="datestamp OAI minimal (date d'ajout ou de "
                            "modification dans l'OPAC, pas annee de "
                            "publication)")
        p.add_argument("--until", metavar="YYYY-MM-DD",
                       help="datestamp OAI maximal")
        p.add_argument("--set", metavar="SETSPEC",
                       help="limite la requete a un datenset (setSpec) ; "
                            "liste via la sous-commande list-sets "
                            "(ex. EuropaeischeGeschichte)")
        p.add_argument("--limit", type=int, metavar="N",
                       help="nombre maximal d'enregistrements a retourner")
        p.add_argument("--workers", type=int, default=1, metavar="N",
                       help="moissonne les pages en parallele avec N workers "
                            "(le serveur encode ses resumptionTokens avec un "
                            "curseur adressable) ; l'ordre de sortie est "
                            "preserve et --delay s'applique par worker, soit "
                            "un debit global ~N/--delay (le serveur sature "
                            "vers ~2x ; au-dela, on le charge sans gain) ; "
                            "une suppression pendant le moissonnage peut "
                            "decaler les pages : dedupliquer par identifiant "
                            "apres coup si le depot evolue (defaut : "
                            "%(default)s)")
        p.add_argument("--jsonl", metavar="FICHIER",
                       help="ecrit les enregistrements en JSONL dans FICHIER "
                            "(append) au lieu de la sortie standard")

    sub.add_parser("identify",
                   help="informations generales du depot (repositoryName, "
                        "baseURL, earliestDatestamp, deletedRecord, "
                        "granularity, ...)")
    sub.add_parser("list-sets",
                   help="liste des datensets/katalogs disponibles "
                        "(setSpec + setName)")
    p = sub.add_parser("list-metadata-formats",
                       help="formats de metadonnees disponibles (globalement "
                            "ou pour une notice donnee)")
    p.add_argument("--identifier", metavar="OPAC-ID",
                   help="limite la liste des formats a cette notice "
                        "(optionnel)")

    p = sub.add_parser("get-record",
                       help="recupere une notice individuelle par son "
                            "identifiant OPAC")
    p.add_argument("identifier", metavar="OPAC-ID",
                   help="identifiant OPAC de la notice (ex. 524395)")
    p.add_argument("--prefix", default="oai_dc", choices=DC_PREFIXES,
                   help="format de sortie : oai_dc, oai_marc ou bibtex "
                        "(defaut : %(default)s)")

    p = sub.add_parser(
        "list-records",
        help="moissonne des notices completes (headers + metadonnees), "
             "suit automatiquement les resumptionTokens ; les notices "
             "supprimees (deletedRecord=transient) sortent avec "
             "status=deleted, sans metadonnees")
    add_harvest_args(p)
    p.add_argument("--language", metavar="CODES",
                   help="codes dc:language separes par des virgules "
                        "(ger,fre,...) ; filtre cote client, exige oai_dc")
    p.add_argument("--query",
                   help="recherche plein texte (titre+sujet+auteur), ET "
                        "logique ; filtre cote client, exige oai_dc")
    p.add_argument("--published-after", type=int, metavar="ANNEE",
                   help="annee de publication minimale (dc:date) ; filtre "
                        "cote client, exige oai_dc")
    p.add_argument("--markdown", metavar="FICHIER",
                   help="rapport markdown dans FICHIER (en plus de stdout "
                        "ou --jsonl)")
    p = sub.add_parser(
        "list-identifiers",
        help="moissonne uniquement les headers (identifiants, datestamps, "
             "sets), plus leger que list-records ; les filtres cote client "
             "ne sont pas disponibles (pas de metadonnees)")
    add_harvest_args(p)

    p = sub.add_parser("latest", help="digest : notices recentes + filtres")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--since", help="datestamp >= YYYY-MM-DD")
    g.add_argument("--last", type=int, help="N notices les plus recentes")
    p.add_argument("--prefix", default="oai_dc", choices=LIST_PREFIXES,
                   help="format de metadonnees ; les filtres ci-dessous "
                        "exigent oai_dc (defaut : %(default)s)")
    p.add_argument("--set", metavar="SETSPEC",
                   help="setSpec pour filtrer cote serveur (ex. "
                        "EuropaeischeGeschichte ; liste via list-sets)")
    p.add_argument("--language", metavar="CODES",
                   help="codes dc:language separes par des virgules (ger,fre,...)")
    p.add_argument("--query",
                   help="recherche plein texte (titre+sujet+auteur), ET logique")
    p.add_argument("--published-after", type=int,
                   help="annee de publication minimale (dc:date)")
    p.add_argument("--limit", type=int, help="nombre max de notices en sortie")
    p.add_argument("--max-pages-per-day", type=int, default=50,
                   help="garde-fou pour --last sur les jours de migration "
                        f"massive (1 page = {PAGE_SIZE} notices)")
    p.add_argument("--lookback-days", type=int, default=730,
                   help="pour --last : nb max de jours explores vers le passe")
    p.add_argument("--jsonl", help="sortie JSONL dans ce fichier")
    p.add_argument("--markdown", help="rapport markdown dans ce fichier")

    args = parser.parse_args(argv)
    client = RIOpacClient(base_url=args.base_url, delay=args.delay)

    try:
        if args.command == "identify":
            _print_json(client.identify())
        elif args.command == "list-sets":
            _print_json(client.list_sets())
        elif args.command == "list-metadata-formats":
            _print_json(client.list_metadata_formats(args.identifier))
        elif args.command == "get-record":
            _print_json(client.get_record(args.identifier, args.prefix))
        elif args.command == "list-records":
            languages = ([lang for lang in args.language.split(",")]
                         if args.language else None)
            matcher = None
            if languages or args.query or args.published_after is not None:
                if args.prefix != "oai_dc":
                    print("Erreur : --language/--query/--published-after sont "
                          "des filtres cote client sur les metadonnees "
                          "DublinCore ; relancez avec --prefix oai_dc.",
                          file=sys.stderr)
                    return 2
                matcher = RecordMatcher(languages=languages, query=args.query,
                                        published_after=args.published_after)
            fh = open(args.jsonl, "a", encoding="utf-8") if args.jsonl else None
            collected = [] if args.markdown else None
            try:
                n = 0
                for rec in client.list_records(prefix=args.prefix,
                                                from_=args.from_,
                                                until=args.until,
                                                set_=args.set, limit=None,
                                                workers=args.workers):
                    # avec des filtres, les notices supprimees (sans
                    # metadonnees) sont ecartees ; sans filtre on les garde
                    if matcher is not None and not matcher.matches(rec):
                        continue
                    n += 1
                    if collected is not None:
                        collected.append(rec)
                    if fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    else:
                        _print_json(rec)
                    # avec des filtres, --limit compte les notices en SORTIE
                    # (pas les notices examinees cote serveur)
                    if args.limit is not None and n >= args.limit:
                        break
                print(f"-- {n} enregistrement(s)", file=sys.stderr)
            finally:
                if fh:
                    fh.close()
            if args.markdown:
                datestamps = [r["datestamp"] for r in collected
                              if r.get("datestamp")]
                stats = {"count": len(collected),
                         "filters": matcher.describe() if matcher else {},
                         "since": args.from_, "last": None, "set": args.set}
                if datestamps:
                    stats["datestamp_min"] = min(datestamps)
                    stats["datestamp_max"] = max(datestamps)
                if args.prefix == "oai_dc":
                    stats["by_language"] = _count_by(collected, "language")
                    stats["by_type"] = _count_by(collected, "type")
                with open(args.markdown, "w", encoding="utf-8") as md:
                    md.write(markdown_report(collected, stats) + "\n")
        elif args.command == "list-identifiers":
            fh = open(args.jsonl, "a", encoding="utf-8") if args.jsonl else None
            try:
                n = 0
                for item in client.list_identifiers(prefix=args.prefix,
                                                     from_=args.from_,
                                                     until=args.until,
                                                     set_=args.set,
                                                     limit=args.limit,
                                                     workers=args.workers):
                    n += 1
                    if fh:
                        fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                    else:
                        _print_json(item)
                print(f"-- {n} enregistrement(s)", file=sys.stderr)
            finally:
                if fh:
                    fh.close()
        elif args.command == "latest":
            languages = ([lang for lang in args.language.split(",")]
                         if args.language else None)
            records, stats = client.latest(
                since=args.since, last=args.last, prefix=args.prefix,
                set_=args.set, languages=languages, query=args.query,
                published_after=args.published_after, limit=args.limit,
                max_pages_per_day=args.max_pages_per_day,
                lookback_days=args.lookback_days)
            fh = open(args.jsonl, "a", encoding="utf-8") if args.jsonl else None
            try:
                for rec in records:
                    if fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    else:
                        _print_json(rec)
            finally:
                if fh:
                    fh.close()
            if args.markdown:
                with open(args.markdown, "w", encoding="utf-8") as md:
                    md.write(markdown_report(records, stats) + "\n")
            print(f"-- {stats['count']} notice(s) retenue(s)", file=sys.stderr)
            print(f"-- stats : {json.dumps(stats, ensure_ascii=False)}",
                  file=sys.stderr)
    except OAIPMHError as exc:
        print(f"Erreur OAI-PMH [{exc.code}]: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
