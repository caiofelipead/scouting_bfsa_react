# Graphics Packs (sortitoutsi.net)

Este diretório armazena imagens de faces e logos importadas de graphics packs
do sortitoutsi.net (ou outras fontes).

## Estrutura

```
graphics_packs/
├── faces/          # Fotos de jogadores (nome normalizado como chave)
│   ├── lionel messi.png
│   ├── cristiano ronaldo.png
│   └── ...
├── logos/          # Escudos de clubes (nome normalizado como chave)
│   ├── flamengo.png
│   ├── palmeiras.png
│   └── ...
└── README.md
```

## Como importar packs do sortitoutsi.net

### 1. Baixar os packs

- **Logos**: https://sortitoutsi.net/graphics/style/25/fmg-standard-logos
- **Faces**: https://sortitoutsi.net/graphics/style/1/cut-out-player-faces

### 2. Extrair o ZIP

Extraia o conteúdo do ZIP baixado em uma pasta temporária.

### 3. Criar arquivo de mapeamento

Os packs do sortitoutsi usam IDs únicos do Football Manager como nomes de arquivo
(ex: `85178649.png`). Para importar, você precisa de um CSV que mapeie esses IDs
para nomes reais.

**Para faces** — crie `fm_faces_mapping.csv`:
```csv
uid,player_name,team_name
85178649,Lionel Messi,Inter Miami
...
```

**Para logos** — crie `fm_logos_mapping.csv`:
```csv
uid,team_name
131,Flamengo
...
```

Você pode exportar esses mapeamentos do FM Editor (Ferramentas > Exportar dados)
ou usar databases da comunidade FM.

### 4. Executar o script de importação

```bash
# Importar faces
python scripts/import_graphics_pack.py faces \
    --pack-dir /caminho/para/sortitoutsi/faces \
    --mapping fm_faces_mapping.csv

# Importar logos
python scripts/import_graphics_pack.py logos \
    --pack-dir /caminho/para/sortitoutsi/logos \
    --mapping fm_logos_mapping.csv

# Importar logos diretamente (sem mapeamento FM) — basta nomear os arquivos
# com o nome do time e colocar em graphics_packs/logos/
```

### 5. Importação manual (sem script)

Se preferir, basta renomear os arquivos PNG com o nome do jogador/time
(em minúsculas) e colocar nos diretórios `faces/` ou `logos/`:

```bash
# Exemplo
cp minha_foto.png graphics_packs/faces/lionel messi.png
cp meu_escudo.png graphics_packs/logos/flamengo.png
```

O sistema normaliza os nomes automaticamente (remove acentos, minúsculas).
