# Syntezator mowy w AP

AP wywołuje syntezator przez komendę `milena_say słowo1 słowo2 ...` (osobne argumenty, nie jeden string). Komenda musi blokować do końca odtwarzania - AP polega na tym przy `say(wait=True)`.

## Milena (domyślna)

Stary syntezator (~2010), zainstalowany w `/usr/local/bin/milena_say`. Działa, ale brzmi niewyraźnie.

## Piper TTS + głos Gosia (zalecana zamiana)

Neural TTS, głos pl_PL-gosia, brzmi naturalnie. Działa offline. Testowane na Ubuntu 20.04.

**Uwagi przed instalacją:**
- `pip3 install piper-tts` nie działa (brak `piper-phonemize` dla tej platformy) - używać binary.
- Repo przeniesione do `github.com/OHF-Voice/piper1-gpl`, ale binary z `rhasspy/piper` 2023.11.14-2 działają na Ubuntu 20.04.
- espeak-ng i festival z polskim brzmią gorzej niż milena - nie warto.

### Instalacja

```bash
# 1. Binary piper (Ubuntu 20.04 x86_64)
mkdir -p ~/piper && cd ~/piper
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar xf piper_linux_x86_64.tar.gz
# binary: ~/piper/piper/piper

# 2. Polski głos Gosia medium (~60 MB)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx.json

# 3. Test
echo "Ala ma kota" | ~/piper/piper/piper --model ~/piper/pl_PL-gosia-medium.onnx --output_file /tmp/test.wav
aplay /tmp/test.wav
```

### Podmiana milena_say

```bash
# Backup oryginału
sudo cp /usr/local/bin/milena_say /usr/local/bin/milena_say.orig
```

Treść nowego `/usr/local/bin/milena_say`:
```bash
#!/bin/bash
echo "$*" | /home/radoslaw/piper/piper/piper \
  --model /home/radoslaw/piper/pl_PL-gosia-medium.onnx \
  --output_file /tmp/milena_say_out.wav 2>/dev/null
aplay -q /tmp/milena_say_out.wav 2>/dev/null
```

```bash
sudo chmod +x /usr/local/bin/milena_say
```

`aplay` blokuje do końca odtwarzania - ważne dla `say(wait=True)` w AP.

### Przywrócenie mileny

```bash
sudo cp /usr/local/bin/milena_say.orig /usr/local/bin/milena_say
```
