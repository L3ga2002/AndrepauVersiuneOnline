# ANDREPAU POS - Aplicatie Desktop (Electron)

## Avantaje fata de versiunea PWA (browser)
- **Bonuri fiscale OFFLINE** - comunica direct cu bridge-ul local, fara internet
- **Auto-start bridge** - porneste automat fiscal_bridge.py
- **Fara restrictii browser** - nu mai e nevoie de cloud polling pentru casa de marcat
- **Performanta mai buna** - aplicatie nativa Windows

## Arhitectura Desktop vs PWA

### PWA (versiunea actuala - browser):
```
React App (HTTPS) --> Cloud API --> Bridge polls --> Printer
                      ^ Necesita internet!
```

### Electron (versiunea desktop):
```
React App (Electron) --> Direct HTTP localhost:5555 --> Bridge --> Printer
                         ^ Fara internet necesar!
```

## Cerinte
- Windows 10/11
- Node.js 18+ (pentru build)
- Python 3.8+ (pentru fiscal_bridge.py)
- SuccesDrv instalat in folderul utilizatorului

## Setup Development

```bash
cd frontend

# Instaleaza dependentele Electron
yarn add --dev electron electron-builder concurrently wait-on

# Ruleaza in mod development
yarn electron-dev
```

## Build pentru Productie

```bash
cd frontend

# 1. Build React app
yarn build

# 2. Build installer Windows (.exe)
yarn electron-build
```

Rezultatul va fi in `frontend/dist-electron/` - un installer `.exe` gata de distribuit.

## Cum functioneaza offline

In Electron, React detecteaza `window.electronBridge` si foloseste comunicare directa:

```javascript
// In React (POSPage.js):
if (window.electronBridge) {
  // Direct la bridge local - FARA internet
  const result = await window.electronBridge.printReceipt(data);
} else {
  // PWA mode - prin cloud API (necesita internet)
  const result = await fetch(`${API_URL}/fiscal/queue`, ...);
}
```

## Structura Fisiere Electron
```
frontend/
  electron/
    main.js      - Procesul principal Electron (comunica cu bridge-ul)
    preload.js   - Expune functii catre React (window.electronBridge)
  electron-builder.json - Configurare build/packaging
```

## Note
- Aplicatia functioneaza si ca PWA si ca desktop - acelasi cod React
- In Electron, bridge-ul poate fi pornit automat la start
- Datele (produse, vanzari) sunt tot pe cloud (MongoDB) - doar comunicarea cu imprimanta e locala
- Pentru offline COMPLET (si fara cloud), ar trebui adaugat IndexedDB + sync
