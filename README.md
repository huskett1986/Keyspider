# Keyspider

Keyspider is a security-focused spidering tool for SMB file shares and web applications.

It is designed for large internal environments where manually reviewing file shares or web content would be impractical. Keyspider can recursively search filenames and file contents for user-defined keywords, generate directory maps for offline review, and crawl web applications while saving matching HTML pages locally.

## Features

- Recursive keyword searching across mounted SMB shares
- Search by:
  - filename
  - file content
  - both filename and content
- Minimum keyword occurrence filtering
- HTML output with clickable `file://` links
- Directory tree generation for offline review
- Same-domain web crawling
- Local saving of matching HTML pages
- Automatic Python virtual environment creation
- Automatic dependency installation

## Requirements

### Linux

Keyspider is primarily designed for Linux.

For SMB share searching, mount the target share using `cifs-utils` before running Keyspider.

Example:

```bash
sudo mount -t cifs //server/share /mnt/share
