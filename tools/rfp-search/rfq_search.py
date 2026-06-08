#!/usr/bin/env python3
"""
Language Services Procurement Search — ToosPoint Consulting
Unified search for RFI / RFP / RFQ across SAM.gov and Grants.gov.
Open/active opportunities only.
"""

import json, os, re, csv, io, threading, webbrowser, urllib.parse
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "rfp_config.json")

LANGUAGE_NAICS = {
    "541930": "Translation & Interpretation Services",
    "611630": "Language Schools",
    "519190": "Other Information Services",
}

# SAM.gov notice types per mode — open solicitations only, never award notices
MODE_NOTICE_TYPES = {
    "rfi": ["r", "s"],          # Sources Sought, Special Notice
    "rfp": ["o", "k", "p"],     # Solicitation, Combined, Pre-Solicitation
    "rfq": ["o", "k"],          # Solicitation, Combined (simplified acquisitions)
}

MODE_LABELS = {
    "rfi": "Request for Information",
    "rfp": "Request for Proposal",
    "rfq": "Request for Quotation",
}

PRESET_KEYWORDS = [
    "language services",
    "translation services",
    "interpretation services",
    "document translation",
    "oral interpretation",
    "over the phone interpretation",
    "video remote interpreting",
    "sign language interpreting",
    "court interpretation",
    "localization services",
    "transcription services",
    "language access",
    "multilingual services",
    "541930",
]

# ─── Config ───────────────────────────────────────────────────────────────────

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"sam_api_key": "", "max_results": 25}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── HTTP Session ─────────────────────────────────────────────────────────────

def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "ToosPoint-Procurement-Search/1.0"})
    return s

SESSION = make_session()

# ─── SAM.gov ──────────────────────────────────────────────────────────────────

def search_sam(keyword, date_from, date_to, notice_types, naics, api_key, max_results):
    results = []
    if not api_key:
        return results, "SAM.gov requires an API key — add yours in Settings."

    try:
        df = datetime.strptime(date_from, "%Y-%m-%d").strftime("%m/%d/%Y")
        dt = datetime.strptime(date_to,   "%Y-%m-%d").strftime("%m/%d/%Y")
    except Exception:
        df, dt = date_from, date_to

    params = {
        "api_key":    api_key,
        "keyword":    keyword,
        "postedFrom": df,
        "postedTo":   dt,
        "ptype":      ",".join(notice_types),
        "active":     "Yes",
        "limit":      min(max_results, 100),
        "offset":     0,
        "sortBy":     "-modifiedDate",
    }
    if naics:
        params["naics"] = naics

    try:
        r = SESSION.get("https://api.sam.gov/opportunities/v2/search",
                        params=params, timeout=30)
        r.raise_for_status()
        for opp in r.json().get("opportunitiesData", []):
            if opp.get("type", "").lower() in ("award notice", "award"):
                continue
            deadline = opp.get("responseDeadLine") or opp.get("archiveDate", "")
            org = (opp.get("fullParentPathName") or
                   (opp.get("organizationHierarchy") or [{}])[-1].get("name", ""))
            results.append({
                "title":      opp.get("title", ""),
                "agency":     org,
                "source":     "SAM.gov",
                "posted":     _fmt_date(opp.get("postedDate", "")),
                "deadline":   _fmt_date(deadline),
                "type":       opp.get("type", ""),
                "naics":      opp.get("naicsCode", ""),
                "value":      "",
                "set_aside":  opp.get("typeOfSetAside", ""),
                "link":       f"https://sam.gov/opp/{opp.get('noticeId','')}/view",
                "description":(opp.get("description") or "")[:2000],
                "notice_id":  opp.get("noticeId", ""),
                "sol_number": opp.get("solicitationNumber", ""),
            })
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 0
        if code == 401: return results, "SAM.gov: Invalid API key."
        if code == 403: return results, "SAM.gov: API key lacks permission."
        return results, f"SAM.gov error {code}."
    except Exception as e:
        return results, f"SAM.gov error: {e}"

    return results, None

# ─── Grants.gov ───────────────────────────────────────────────────────────────

def search_grants(keyword, date_from, date_to, max_results):
    results = []
    try:
        r = SESSION.post(
            "https://apply07.grants.gov/grantsws/rest/opportunities/search/",
            json={
                "keyword":        keyword,
                "oppStatuses":    "forecasted|posted",
                "rows":           min(max_results, 50),
                "startRecordNum": 0,
                "sortBy":         "openDate|desc",
                "dateRange":      "custom",
                "startDate":      date_from,
                "endDate":        date_to,
            }, timeout=30)
        r.raise_for_status()
        for opp in r.json().get("oppHits", []):
            results.append({
                "title":      opp.get("title", ""),
                "agency":     opp.get("agencyName", ""),
                "source":     "Grants.gov",
                "posted":     _fmt_date(opp.get("openDate", "")),
                "deadline":   _fmt_date(opp.get("closeDate", "")),
                "type":       opp.get("oppStatus", ""),
                "naics":      "",
                "value":      _fmt_value(opp.get("awardCeiling")),
                "set_aside":  "",
                "link":       f"https://www.grants.gov/search-results-detail/{opp.get('id','')}",
                "description":(opp.get("synopsis") or "")[:2000],
                "notice_id":  str(opp.get("id", "")),
                "sol_number": opp.get("number", ""),
            })
    except Exception as e:
        return results, f"Grants.gov error: {e}"
    return results, None

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fmt_date(val):
    if not val: return ""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try: return datetime.strptime(str(val)[:19], fmt).strftime("%Y-%m-%d")
        except Exception: continue
    return str(val)[:10]

def _fmt_value(val):
    if val is None: return ""
    try:
        v = float(val)
        if v >= 1_000_000: return f"${v/1_000_000:.1f}M"
        if v >= 1_000:     return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"
    except Exception: return str(val)

def dedup(results):
    seen, out = set(), []
    for r in results:
        key = re.sub(r'\W', '', r["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key); out.append(r)
    return out

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    cfg = load_config()
    return render_template("rfq_index.html",
        presets=PRESET_KEYWORDS,
        naics_codes=LANGUAGE_NAICS,
        has_sam_key=bool(cfg.get("sam_api_key")),
        mode_labels=MODE_LABELS,
    )

@app.route("/api/search", methods=["POST"])
def api_search():
    body      = request.get_json()
    keyword   = body.get("keyword", "").strip()
    mode      = body.get("mode", "rfp").lower()
    date_from = body.get("date_from", (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))
    date_to   = body.get("date_to",   datetime.now().strftime("%Y-%m-%d"))
    sources   = body.get("sources",   ["sam", "grants"])
    naics     = body.get("naics",     "541930")
    max_res   = int(body.get("max_results", 25))

    # Use mode-specific notice types (user can override via body)
    notice_types = body.get("notice_types") or MODE_NOTICE_TYPES.get(mode, ["o", "k"])

    cfg     = load_config()
    api_key = cfg.get("sam_api_key", "")

    all_results, errors = [], []

    def run(fn, *args):
        res, err = fn(*args)
        all_results.extend(res)
        if err: errors.append(err)

    threads = []
    if "sam" in sources:
        threads.append(threading.Thread(
            target=run,
            args=(search_sam, keyword, date_from, date_to, notice_types, naics, api_key, max_res)))
    if "grants" in sources:
        threads.append(threading.Thread(
            target=run,
            args=(search_grants, keyword, date_from, date_to, max_res)))

    for t in threads: t.daemon = True; t.start()
    for t in threads: t.join(timeout=35)

    return jsonify({"results": dedup(all_results), "errors": errors, "total": len(all_results)})

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        save_config(request.get_json())
        return jsonify({"ok": True})
    return jsonify(load_config())

@app.route("/api/export/csv", methods=["POST"])
def export_csv():
    body    = request.get_json()
    results = body.get("results", [])
    mode    = body.get("mode", "rfp")
    si      = io.StringIO()
    fields  = ["title","agency","source","posted","deadline","type","value","sol_number","link"]
    w = csv.DictWriter(si, fieldnames=fields, extrasaction="ignore")
    w.writeheader(); w.writerows(results)
    fname = f"{mode}_language_services_{datetime.now().strftime('%Y-%m-%d')}.csv"
    return Response(si.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"})

if __name__ == "__main__":
    url = "http://127.0.0.1:5051"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"\n  ToosPoint Language Services Search → {url}\n")
    app.run(host="127.0.0.1", port=5051, debug=False)
