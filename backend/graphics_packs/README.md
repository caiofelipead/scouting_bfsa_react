# Graphics Packs (sortitoutsi.net)

Este diretorio armazena imagens de faces e logos importadas de graphics packs
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

Extraia o conteudo do ZIP baixado em uma pasta temporaria.

### 3. Obter dados de mapeamento FM UID → Nome

Os packs usam IDs unicos do Football Manager (ex: `19024412.png` = Neymar).
Voce precisa de um CSV com esses mapeamentos.

**Opcoes para obter o CSV:**

a) **FM Editor** — Abra o FM, va em Ferramentas > Exportar dados. Exporte jogadores/times
   com colunas `uid` e `name`.

b) **fmref.com** — Site de busca do sortitoutsi. Busque jogadores por nome e
   pressione "c" para copiar o UID. Util para buscar jogadores individuais.
   Ex: Buscar "Neymar" → UID `19024412`

c) **Databases da comunidade FM** — Existem exports da database do FM em sites como
   fmscout.com, sortitoutsi.net/football-manager, etc.

### 4. Gerar mapeamento automatico (recomendado)

Use o script `build_fmref_mapping.py` para cruzar automaticamente os jogadores
do dashboard com a database do FM usando fuzzy matching:

```bash
cd backend

# Gerar mapeamento de faces
python scripts/build_fmref_mapping.py faces \
    --fm-data /caminho/para/fm_people.csv \
    --pack-dir /caminho/para/sortitoutsi/faces \
    --min-score 85

# Gerar mapeamento de logos
python scripts/build_fmref_mapping.py logos \
    --fm-data /caminho/para/fm_clubs.csv \
    --pack-dir /caminho/para/sortitoutsi/logos \
    --min-score 80
```

O script:
1. Le os jogadores/times do dashboard (`fotos_jogadores_clubes_ligas.csv`)
2. Le a database do FM (seu CSV exportado)
3. Faz fuzzy matching por nome (usando rapidfuzz)
4. Gera `fm_faces_mapping.csv` ou `fm_logos_mapping.csv` pronto para importar
5. Lista os jogadores sem match para voce buscar manualmente no fmref.com

### 5. Importar as imagens

Com o mapping CSV gerado, execute o import:

```bash
# Importar faces
python scripts/import_graphics_pack.py faces \
    --pack-dir /caminho/para/sortitoutsi/faces \
    --mapping fm_faces_mapping.csv

# Importar logos
python scripts/import_graphics_pack.py logos \
    --pack-dir /caminho/para/sortitoutsi/logos \
    --mapping fm_logos_mapping.csv
```

### 6. Importacao manual (sem script)

Se preferir, basta renomear os arquivos PNG com o nome do jogador/time
(em minusculas) e colocar nos diretorios `faces/` ou `logos/`:

```bash
# Exemplo
cp minha_foto.png graphics_packs/faces/lionel messi.png
cp meu_escudo.png graphics_packs/logos/flamengo.png
```

Para buscar UIDs individuais no fmref.com:
1. Acesse https://fmref.com
2. Digite o nome do jogador (ex: "neymar")
3. Encontre o jogador correto nos resultados
4. Pressione "c" para copiar o UID (ex: `19024412`)
5. Localize `19024412.png` no pack do sortitoutsi
6. Renomeie para o nome normalizado e copie para `faces/`

O sistema normaliza os nomes automaticamente (remove acentos, minusculas).

## Fluxo completo resumido

```
sortitoutsi.net          fmref.com / FM Editor
     |                        |
     v                        v
 Pack ZIP                 FM database CSV
(19024412.png)           (uid,name,team)
     |                        |
     +--- build_fmref_mapping.py ---+
                    |
                    v
           fm_faces_mapping.csv
          (uid,player_name,team_name)
                    |
                    v
         import_graphics_pack.py
                    |
                    v
          graphics_packs/faces/
         (lionel messi.png, etc)
                    |
                    v
          Dashboard automaticamente
          usa as imagens locais!
```
