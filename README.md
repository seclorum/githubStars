# Star Map

A visual explorer for large collections of GitHub starred repositories.

## v0.1

The first version is deliberately self-contained:

- Svelte
- Vite
- D3
- Canvas rendering
- 3,247 deterministic mock repositories
- heuristic categorization
- category filtering
- repository search
- repository inspector
- pinning
- local IndexedDB persistence
- GitHub Pages deployment

GitHub authentication and live repository data are intentionally deferred to v0.2.

## Development

```bash
npm install
npm run dev
````

Then open the local URL shown by Vite.

## Production build

```bash
npm run build
npm run preview
```

## GitHub Pages

The repository includes a GitHub Actions workflow.

In the GitHub repository:

1. Open **Settings → Pages**.
2. Set the source to **GitHub Actions**.
3. Push to `main`.
4. GitHub Actions will build and deploy the site.

## Architecture

The important boundary is between the repository data model and the visualization.

The current application uses:

```text
Mock repositories
      ↓
Repository model
      ↓
Categorizer
      ↓
D3 layout
      ↓
Canvas renderer
      ↓
Svelte UI
```

The intended next step is to replace the mock provider with:

```text
GitHub OAuth
      ↓
GitHub /user/starred
      ↓
Repository model
      ↓
same application
```

This keeps the visualization independent of GitHub's API.


