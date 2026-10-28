# Publishing to github.com

1. Create an empty repository on github.com (no README), e.g. `legendary-sports-theme`.
2. From this folder:

```bash
git init
git add .
git commit -m "Legendary sports theme generator: script, samples, docs"
git branch -M main
git remote add origin https://github.com/<your-user>/legendary-sports-theme.git
git push -u origin main
```

The `samples/` folder is about 23 MB of WAV files, which is within GitHub's
per-file limit (100 MB). Convert to MP3/FLAC if you want a lighter repo.
