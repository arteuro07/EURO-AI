# EURO AI

Assistant personnel hybride piloté depuis Termux, avec calculs exécutés par GitHub Actions.

## État actuel
- Dépôt public.
- Moteur Python minimal.
- Règles propriétaires en JSON.
- Workflow GitHub déclenchable manuellement et planifié.

## Sécurité
- Ne jamais publier de tokens, clés API ou mots de passe.
- Ne pas exécuter de commandes shell arbitraires fournies par l'utilisateur.
- Les actions externes doivent demander une confirmation explicite.

## Lancement local
```bash
python core/engine.py "Bonjour EURO AI"
```

Le modèle de langage, l'interface Cloudflare et l'application Android seront ajoutés après validation du moteur de base.
