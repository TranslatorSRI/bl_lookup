# Biolink Model lookup service

## deployment

### local

```bash
pip install -r requirements.txt
./main.py --port 8144
```

### Docker

```bash
docker build -t blm_lookup .
docker run -p 8144:8144 blm_lookup --port 8144
```
