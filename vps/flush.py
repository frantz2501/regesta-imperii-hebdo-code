#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Purge horaire : spool -> chunk gzippe -> commit git -> push -> purge.

Principe: les pages presentes dans spool/ (ecritures atomiques du
moissonneur) et non encore purgees sont groupees en un RUN CONTIGU a
partir de la premiere page manquante (l'ordre des identifiants est
sequentiel, il faut des pages contigues pour la deduplication en
frontiere). Le chunk est committe localement (perte de donnees
impossible meme si GitHub est indisponible), les pages sont alors
supprimees du spool, puis le push est tente ; en cas d'echec, les
commits restent en attente et le push est retente a la prochaine heure.
"""

import datetime as dt
import gzip
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SPOOL = os.path.join(BASE, "spool")
WORKDIR = os.path.join(BASE, "work", "regesta-imperii-fond")
FOND_DIR = os.path.join(WORKDIR, "fond")
STATE_FILE = os.path.join(BASE, "state.json")
REMOTE = "ssh://git@github.com/frantz2501/regesta-imperii-fond.git"
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_github_fond")
GIT_SSH_COMMAND = (f"ssh -i {SSH_KEY} -o IdentitiesOnly=yes "
                   f"-o StrictHostKeyChecking=accept-new")
MAX_PAGES_PER_CHUNK = 1000  # ~40-45 Mo gz par chunk


def log(msg):
    ts = dt.datetime.now().isoformat(timespec="seconds")
    print(f"{ts} {msg}", flush=True)


def git(args, check=True, input_text=None):
    env = dict(os.environ, GIT_SSH_COMMAND=GIT_SSH_COMMAND)
    proc = subprocess.run(["git", "-C", WORKDIR] + args, env=env,
                         capture_output=True, text=True, input=input_text)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {args} : rc={proc.returncode} "
                            f"stderr={proc.stderr.strip()[:400]}")
    return proc


def init_workdir():
    if not os.path.isdir(FOND_DIR):
        os.makedirs(FOND_DIR, exist_ok=True)
    if not os.path.isdir(os.path.join(WORKDIR, ".git")):
        log("initialisation du depot git local (remote passee, "
            "push retente a chaque heure jusqu'a creation du repo/cle)")
        subprocess.run(["git", "init", "-b", "main", WORKDIR],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", WORKDIR, "remote", "add", "origin",
                        REMOTE], capture_output=True, check=False)
        git(["config", "user.name", "ri-opac-bot"], check=False)
        git(["config", "user.email", "heimdal@cyberchinois.eu"], check=False)
        git(["config", "core.sshCommand", GIT_SSH_COMMAND], check=False)
        readme = os.path.join(WORKDIR, "README.md")
        if not os.path.exists(readme):
            with open(readme, "w", encoding="utf-8") as fh:
                fh.write(
                    "# regesta-imperii-fond\n\n"
                    "Fond complet du RI OPAC (Regesta Imperii, ~3,13 M "
                    "notices) moissonne via l'interface OAI-PMH "
                    "`https://opac.regesta-imperii.de/api/oai`, "
                    "format `oai_dc`, en chunks JSONL gzippes "
                    "(`fond/chunk_*.jsonl.gz`, ~100 pages de 100 notices "
                    "chacun, identifiants croissants).\n\n"
                    "Etat d'avancement : `fond/state.json`. "
                    "Source : Regesta Imperii OPAC, licence CC BY 4.0.\n")


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"last_page_flushed": 0, "chunks": []}


def save_state(state):
    with open(STATE_FILE + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(STATE_FILE + ".tmp", STATE_FILE)


def spool_pages():
    out = []
    for name in os.listdir(SPOOL):
        m = re.fullmatch(r"page_(\d+)\.jsonl", name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def contiguous_run(pages, first_needed):
    """Plus grand run contigu de pages a partir de first_needed."""
    present = set(pages)
    run = []
    page = first_needed
    while page in present and len(run) < MAX_PAGES_PER_CHUNK:
        run.append(page)
        page += 1
    return run


def build_chunk(run, chunk_no, state):
    records = 0
    last_id = None
    path = os.path.join(FOND_DIR, f"chunk_{chunk_no:06d}.jsonl.gz")
    import io
    with gzip.open(path, "wb") as raw, \
            io.TextIOWrapper(raw, encoding="utf-8") as out:
        for page in run:
            src = os.path.join(SPOOL, f"page_{page:06d}.jsonl")
            with open(src, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    rid = rec.get("identifier")
                    if rid is not None and rid == last_id:
                        continue  # doublon de frontieres (deletedRecord=transient)
                    last_id = rid
                    out.write(line if line.endswith("\n") else line + "\n")
                    records += 1
    return path, records


def notify_olvid(body):
    """Envoie un message Olvid via le stack train-alert (docker)."""
    script = os.path.join(BASE, "notify_olvid.py")
    if not os.path.isfile(script):
        return False, "notify_olvid.py absent"
    try:
        with open("/opt/train-alert/config.json", encoding="utf-8") as fh:
            discussion_id = json.load(fh)["olvid_discussion_id"]
    except (OSError, ValueError, KeyError) as exc:
        return False, f"config.json train-alert illisible : {exc!r}"
    try:
        with open(script, encoding="utf-8") as fh:
            code = fh.read()
        proc = subprocess.run(
            ["docker", "exec", "-i",
             "-e", f"OLVID_DISCUSSION_ID={discussion_id}",
             "-e", f"MSG_BODY={body}",
             "train-alert-bot-1", "python", "-"],
            input=code, capture_output=True, text=True, timeout=180)
    except Exception as exc:
        return False, f"docker exec : {exc!r}"
    ok = proc.returncode == 0 and "SEND_OK" in proc.stdout
    return ok, (proc.stdout + proc.stderr).strip()[:200]


def main():
    if not os.path.isdir(SPOOL) or not spool_pages():
        log("rien a purger (spool vide)")
        return 0
    init_workdir()
    state = load_state()
    state.setdefault("chunks", [])

    run = contiguous_run(spool_pages(),
                         state.get("next_page_needed",
                                   state.get("last_page_flushed", 0) + 1))
    source = state.get("next_page_needed",
                       state.get("last_page_flushed", 0) + 1)
    if isinstance(source, int) and source < 1:
        source = 1
    if not run:
        log(f"aucun run contigu a partir de la page {source} ; "
            "le moissonneur comblera le trou")
        return 0

    chunk_no = len(state["chunks"]) + 1
    log(f"chunk {chunk_no}: pages {run[0]}..{run[-1]}")
    path, records = build_chunk(run, chunk_no, state)

    state["chunks"].append({
        "chunk": chunk_no,
        "pages": [run[0], run[-1]],
        "records": records,
        "file": os.path.basename(path),
        "created": dt.datetime.now().isoformat(timespec="seconds"),
    })
    state["last_page_flushed"] = run[-1]
    state["next_page_needed"] = run[-1] + 1

    fond_state = {
        "chunks_total": len(state["chunks"]),
        "last_page_flushed": state["last_page_flushed"],
        "total_pages": state.get("total_pages"),
        "records_flushed": sum(c["records"] for c in state["chunks"]),
        "updated": dt.datetime.now().isoformat(timespec="seconds"),
        "source": "https://opac.regesta-imperii.de/api/oai (oai_dc, CC BY 4.0)",
    }
    with open(os.path.join(FOND_DIR, "state.json"), "w",
              encoding="utf-8") as fh:
        json.dump(fond_state, fh, ensure_ascii=False, indent=2)

    git(["add", "fond/"])
    git(["commit", "-m",
         f"fond: chunk {chunk_no:06d} (pages {run[0]}-{run[-1]}, "
         f"{records} notices)"])
    save_state(state)
    # le commit local fait foi : on purge le spool meme si le push echoue
    for page in run:
        try:
            os.remove(os.path.join(SPOOL, f"page_{page:06d}.jsonl"))
        except OSError:
            pass
    log(f"chunk {chunk_no} commite, {records} notices, spool purge "
        f"({len(run)} pages)")

    push = subprocess.run(["git", "-C", WORKDIR, "push", "-u", "origin",
                           "main"],
                          env=dict(os.environ,
                                   GIT_SSH_COMMAND=GIT_SSH_COMMAND),
                          capture_output=True, text=True)
    if push.returncode == 0:
        log(f"push OK ({len(state['chunks'])} chunks sur GitHub)")
        # notification de fin : tout le fond moissonne ET pousse
        total = state.get("total_pages")
        if (total and state["last_page_flushed"] >= int(total)
                and not state.get("notified_complete")):
            body = (f"Moissonnage du fond RI OPAC termine.\n"
                    f"{total} pages ({fond_state['records_flushed']} notices), "
                    f"{len(state['chunks'])} chunks pousses sur "
                    f"frantz2501/regesta-imperii-fond.")
            sent, info = notify_olvid(body)
            if sent:
                state["notified_complete"] = True
                save_state(state)
                log(f"notification Olvid envoyee (fin du fond) : {info}")
            else:
                log(f"notification Olvid en echec, retentee a la prochaine "
                    f"heure : {info}")
    else:
        log(f"push en echec (retente a la prochaine heure) : "
            f"{(push.stderr or push.stdout).strip()[:300]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
