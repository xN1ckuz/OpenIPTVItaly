# 🇮🇹 OpenIPTVItaly

**OpenIPTVItaly** is an **open-source, public and curated Italian IPTV playlist**, designed to become **the reference playlist for free-to-air Italian TV channels**.

> 🎯 Goal: quality, reliability and transparency. No broken links, no pay-TV, no DRM.

---

## 📺 Content

The playlist includes **only publicly available and legally accessible streams**:

* 📡 National and local free-to-air TV channels
* 🧒 Kids channels
* 📰 News
* 🎬 Entertainment
* 🏟️ Free sports
* 📻 Radio (when available)

❌ **Not included**:

* Pay-TV channels
* DRM-protected streams
* Pirated or redistributed content

---

## 🧩 Playlist Structure

The playlist follows common IPTV standards:

* Consistent `tvg-id` for EPG matching
* Official `tvg-name`
* High-quality `tvg-logo`
* `tvg-chno` (LCN where applicable)

---

## ▶️ Usage

### 🔗 Playlist URL

**Main Playlist (with metadata)**  

Includes full channel metadata and standard playlist structure.

```
https://raw.githubusercontent.com/xN1ckuz/OpenIPTVItaly/refs/heads/main/OpenIPTVItaly.m3u
```

**Minimal Playlist (No EPG)**

Simplified version with no EPG and no external dependencies.  
Recommended for maximum compatibility with basic IPTV players and Smart TVs.

```
https://raw.githubusercontent.com/xN1ckuz/OpenIPTVItaly/refs/heads/main/OpenIPTVItaly_No_EPG.m3u
```

Both playlists are compatible with the following IPTV players:

* VLC
* Kodi
* SSIPTV
* IPTV Smarters
* TiviMate
* OttPlayer

---

## 📡 EPG Source
When available, EPG data is obtained from publicly accessible sources provided by **epgshare01.online**.

The EPG is used for informational purposes only and reflects standard TV scheduling
data that is already publicly available.

This project does not access private APIs, restricted services, or proprietary
broadcast systems.

> Note: The **OpenIPTVItaly_No_EPG** playlist does not rely on any EPG source.

## 🐞 Known Issues and Changelog

The following channels do not currently have an IPTV-compatible stream available and are included **only to preserve correct LCN numbering**:

- **Boing Plus (+1 / Channel 45)** *(LCN-only)*
- **Teledue (Channel 12)** *(LCN-only)*
- **Canale 63 (Channel 63 known as CS24.Live)** *(LCN-only)*

All notable changes are documented in **[CHANGELOG.md](CHANGELOG.md)**.

---

## 🤝 Contributing

Contributions are welcome, but **must follow strict rules** to keep the playlist clean and reliable.

Before contributing, please read **CONTRIBUTING.md** (to be published).

Typical contributions:

* Report broken streams
* Propose new **free & legal** channels
* Improve metadata or logos

---

## ⚖️ Legal Disclaimer

This project:

* DOES NOT host any content
* DOES NOT redistribute streams
* Only provides links to publicly available sources

All rights belong to their respective owners.

---

## 📜 License

This project is released under the **MIT License**.

