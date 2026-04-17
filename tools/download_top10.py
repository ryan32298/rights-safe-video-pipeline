import json
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen, urlretrieve

ARTISTS = [
    "Doc Watson","Bruce Cockburn","Tony Rice","Bill Monroe","Lester Flatt",
    "Earl Scruggs","Ralph Stanley","Carter Stanley","Jimmy Martin","J.D. Crowe"
]

def read_json(url):
    with urlopen(url) as r:
        return json.loads(r.read().decode("utf-8"))

def search_artist(artist):
    q = f'(title:("{artist}") OR creator:("{artist}")) AND mediatype:(movies)'
    url = (
        "https://archive.org/advancedsearch.php?"
        f"q={quote_plus(q)}&fl[]=identifier&fl[]=title&rows=5&page=1&output=json"
    )
    return read_json(url).get("response", {}).get("docs", [])

def pick_video(files):
    exts = {".mp4",".webm",".ogv",".mkv",".mov"}
    vids = [f for f in files if Path(f.get("name","")).suffix.lower() in exts]
    vids.sort(key=lambda x: int(x.get("size", 0)), reverse=True)
    return vids[0] if vids else None

def main():
    out = Path.home() / "Desktop" / "rights-safe-test-downloads"
    out.mkdir(parents=True, exist_ok=True)
    manifest = []

    for artist in ARTISTS:
        print("Searching:", artist)
        docs = search_artist(artist)
        if not docs:
            print("  none found")
            continue

        downloaded = False
        for d in docs:
            ident = d.get("identifier")
            title = str(d.get("title", ident or "Unknown"))
            if not ident:
                continue
            meta = read_json(f"https://archive.org/metadata/{ident}")
            f = pick_video(meta.get("files", []))
            if not f:
                continue

            src_name = f["name"]
            ext = Path(src_name).suffix or ".mp4"
            safe_title = "".join(c for c in f"{artist} - {title} (Live)" if c.isalnum() or c in " -_()").strip()
            dst = out / f"{safe_title[:120]}{ext}"
            url = f"https://archive.org/download/{ident}/{quote_plus(src_name)}"
            urlretrieve(url, dst)
            print("  downloaded:", dst.name)
            manifest.append({
                "artist": artist,
                "archive_title": title,
                "suggested_youtube_title": f"{artist} - {title} (Live)",
                "local_path": str(dst),
                "source_url": url
            })
            downloaded = True
            break

        if not downloaded:
            print("  no downloadable video found")

    (out / "download_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Done. Folder:", out)

if __name__ == "__main__":
    main()
