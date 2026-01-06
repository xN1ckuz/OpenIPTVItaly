# Contributing to OpenIPTVItaly

Thank you for your interest in contributing to **OpenIPTVItaly** 🇮🇹📺

This project aims to be a **high‑quality, transparent and community‑driven reference IPTV playlist for Italy**, focused on **free‑to‑air and publicly accessible streams only**.

Please read this document carefully before opening issues or pull requests.

---

## 📌 Project Principles

By contributing, you agree to respect the following principles:

* ✅ **Free‑to‑air content only**
* ❌ **No DRM‑protected, pay‑TV or premium streams**
* ❌ **No cracked, leaked or pirated sources**
* ✅ Streams must be **publicly accessible** and verifiable
* ✅ Metadata must be accurate, consistent and clean

Any contribution violating these principles will be rejected.

---

## 🐞 Reporting Issues

You are welcome to open an issue if you find:

* ❌ Offline or broken streams
* 🔄 Token‑based or unstable URLs
* 🖼 Missing or incorrect logos
* 🔢 Wrong LCN (Logical Channel Number)
* 📝 Metadata errors (`tvg-id`, `tvg-name`, etc.)

### Issue Guidelines

When opening an issue, please include:

* Channel name
* Playlist version (with or without EPG)
* Player used (VLC, Kodi, SSIPTV, etc.)
* Error description (what works / what doesn’t)
* Optional: screenshots or logs

Issues without enough details may be closed.

---

## 🔧 Contributing Streams

Before submitting a new stream:

* Verify that the stream is **legal and free‑to‑air**
* Test it with **at least two different players**
* Ensure it works **without authentication or cookies**
* Prefer **stable URLs** over short‑lived tokenized links

If a stream is known to be unstable, it must be clearly documented as a **known issue**.

---

## 🧾 Playlist Formatting Rules

All channels must include:

* `tvg-id`
* `tvg-name`
* `tvg-logo`
* `tvg-chno` 

Please keep formatting consistent with the existing playlist.

---

## 🔀 Pull Requests

### Before submitting a PR

* Fork the repository
* Create a dedicated branch
* Test your changes locally
* Update documentation if needed

### Pull Request Checklist

* [ ] Streams tested and working
* [ ] No DRM / premium content
* [ ] Metadata validated
* [ ] Playlist formatting respected
* [ ] CHANGELOG updated (if applicable)

Pull requests that do not follow these rules may be rejected.

---

## 🧪 Automated Checks

This repository uses GitHub Actions to:

* Validate playlist links
* Generate releases automatically
* Attach playlist files as release assets

Please ensure your contributions do not break existing automation.

---

## 📣 Community & Credits

* Contributions are welcome and appreciated
* Significant contributors may be credited in the README
* Be respectful and constructive

---

## ⚖️ Legal Disclaimer

This project **does not host any video content**.

It only provides publicly available links found on the web.

If you are a rights holder and believe a link should be removed, please open an issue.

---

Thank you for helping make **OpenIPTVItaly** better 🚀
