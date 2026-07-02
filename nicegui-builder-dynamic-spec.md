# Spec — Rendu dynamique pour nicegui-builder

**Statut :** proposition d'implémentation
**Portée :** trois capacités complémentaires (liaison d'événements, interpolation de valeurs, répétition) reposant sur un *contexte de résolution unifié*.
**Principe directeur :** la lib reste un **constructeur one-shot** (build une fois → rend les refs). On n'introduit **aucun moteur de réactivité** ; on ajoute une primitive de re-rendu de sous-arbre. NiceGUI garde la responsabilité du binding réactif natif.

---

## 0. État actuel (rappel d'ancrage)

- `builder(layout)` parcourt une liste de nœuds via `visit()`, retourne le composant racine avec `.component_refs`.
- `visit()` par nœud : résout `params`/`classes`/`props` via `resolve_context_value(value, ctx)`, instancie via `_render_method_chain` (chaîne de méthodes sur `ui`), applique `classes`/`props`, enregistre la `ref`, puis récursion sur `children`.
- `resolve_context_value` :
  - `"_foo"` → `"foo".format(**ctx)` (chaîne uniquement, remplacement total).
  - `"$mod:func"` → `getattr(import_module(mod), func)(**ctx)` (appel, retour utilisé comme valeur).
- `ctx` = `ContextVar[dict]`. `ensure_builder_runtime(ctx)` crée `ctx["_runtime"] = {"component_refs": {}, "root_component": None}`.
- Pas de gestion d'événements, pas de répétition, pas d'interpolation partielle.

**Faiblesses traitées par cette spec :**
1. Aucun moyen propre de lier un événement à une closure de page (le `$` force le niveau-module + appelle-pour-retourner).
2. Interpolation fragile : sigils `_`/`$` collision-prone, remplacement tout-ou-rien, chaîne seulement.
3. Aucune cardinalité dynamique (impossible de rendre N enfants depuis une liste).

---

## 1. Contexte de résolution unifié (fondation des 3 features)

Étendre la signature publique :

```python
def builder(
    layout,
    *,
    context: dict | None = None,     # données disponibles à l'interpolation
    handlers: dict[str, Callable] | None = None,   # event bindings par nom
    filters: dict[str, Callable] | None = None,    # transformations de valeurs
) -> RootComponent: ...
```

Stockage : à côté de `component_refs` dans le runtime.

```python
runtime = {
    "component_refs": {},
    "root_component": None,
    "handlers": handlers or {},
    "filters": filters or {},
}
```

`context` est fusionné dans le `ctx` racine (les clés utilisateur vivent au même niveau que les variables de scope ; voir §4 pour l'imbrication).

**Mental model utilisateur :** le YAML décrit la *structure* et *quels noms* se branchent. Python fournit le *contexte* (données), les *filtres* (mise en forme) et les *handlers* (comportement).

**Rétrocompat :** tous les nouveaux paramètres sont optionnels. Le comportement actuel est inchangé si aucun n'est fourni. Les sigils `_`/`$` restent supportés (voir §3.4 migration).

---

## 2. Liaison d'événements (priorité 1 — petit, gros gain)

### 2.1 Syntaxe YAML

Nouvelle clé de nœud `on` : mapping `event_name → handler_name`.

```yaml
- button:
    params: { text: Annuler }
    on: { click: cancel }
- input:
    ref: search
    on: { value_change: on_search }
- element:
    on: { keydown.enter: submit }    # event DOM arbitraire toléré
```

### 2.2 Résolution

Pour chaque `(event, name)` après instanciation + application classes/props :

```python
handler = runtime["handlers"].get(name)
if handler is None:
    raise ValueError(
        f"unknown handler {name!r} for event {event!r}; "
        f"available: {sorted(runtime['handlers'])}"
    )
method = getattr(component, f"on_{event}", None)
if callable(method):
    method(handler)          # ui.button → on_click, ui.input → on_value_change
else:
    component.on(event, handler)   # fallback DOM générique
```

### 2.3 Règles de conception

- **Échec fort au build** si le nom est inconnu (cohérent avec le `ValueError` existant sur ref dupliquée). Jamais en silence.
- **Signature du handler :** passer tel quel à NiceGUI (qui tolère déjà 0-arg / 1-arg). Ne pas réinventer.
- **Coexistence avec les refs :** `on` couvre 90 % des cas ; la ref reste l'échappatoire pour manipuler l'objet élément (ex. `set_enabled`).
- **Ordre :** binder l'événement *après* la création du composant (les events sont sur l'instance).

### 2.4 Cas de test

- `on: {click: x}` avec `x` dans handlers → `on_click` appelé une fois avec `x`.
- handler manquant → `ValueError` listant les noms dispo.
- event sans méthode `on_<event>` → passe par `.on(event, handler)`.
- handler nommé utilisé dans une répétition (voir §4.3) reçoit l'item de scope.

---

## 3. Interpolation de valeurs (priorité 2)

### 3.1 Syntaxe — tokens `{{ }}` explicites

Remplace la sémantique des sigils. Dans **toute** valeur de `params`/`classes`/`props` :

```yaml
text: "segment #{{ seg.segment_id }}/{{ count }}"     # substitution partielle + multiple
value: "{{ entry.enabled }}"                           # token unique → objet typé (bool)
classes: "w-full {{ extra_classes }}"
```

### 3.2 Règles de résolution

1. **Substitution partielle et multiple** : chaque `{{ … }}` dans la chaîne est remplacé ; le texte autour est littéral.
2. **Passage typé** : si la valeur est *exactement* un token unique (`"{{ x }}"` sans texte autour), retourner l'objet `x` (bool/int/list/…), pas son `str`. Indispensable pour `value:`, `min:`, `max:`, etc.
3. **Accès attr + item** : `{{ entry.machinex_id }}` puis `{{ row['key'] }}` résolus contre `ctx` (essaie attribut, puis indexation). Évite d'aplatir tous les champs dans `ctx`.
4. **Filtres** : `{{ duration | mmss }}` applique `runtime["filters"]["mmss"](valeur)`. Chaînables : `{{ x | a | b }}`.

### 3.3 Frontière de sécurité (NON négociable)

- **Pas d'eval arbitraire.** Grammaire fermée : `nom`, chemins `.attr` / `['clé']`, et `| filtre` whitelistés.
- Token inconnu → `ValueError` explicite au build (nom + nœud).
- Filtre inconnu → `ValueError` listant les filtres dispo.

### 3.4 Migration / rétrocompat

- Garder `_`/`$` fonctionnels pendant ≥1 version mineure, derrière un `DeprecationWarning`.
- Documenter l'équivalence : `_{x}` → `"{{ x }}"` ; `$mod:func` → privilégier `filters`/`handlers`, conserver `$` comme échappatoire avancée.
- Risque : un littéral contenant `{{` devient ambigu → fournir un échappement (`{{ '{{' }}` ou `\{{`).

### 3.5 Cas de test

- Multi-token dans une chaîne ; token unique typé (bool/list conservés).
- Accès attribut et item ; chemin profond `a.b.c`.
- Filtre simple, filtres chaînés ; filtre/nom inconnu → erreur.
- Échappement d'un `{{` littéral.

---

## 4. Répétition + re-rendu (priorité 3 — relève le plafond)

### 4.1 Nœud `repeat`

```yaml
- repeat:
    in: "{{ segments }}"          # résout vers un itérable depuis ctx
    as: seg                       # nom de l'item dans la scope enfant
    key: "{{ seg.segment_id }}"   # identité stable (refs adressables, diff futur)
    children:
      - row:
          children:
            - label:  { params: { text: "#{{ seg.segment_id }}" } }
            - button: { params: { text: Justify }, on: { click: justify } }
```

### 4.2 Sémantique de scope

Pour chaque `item` de l'itérable :
1. Dériver une **scope enfant** = copie du `ctx` courant + `{as_name: item, "$index": i, "$key": key_value}`.
2. Visiter `children` sous cette scope (mêmes mécanismes d'interpolation/handlers).
3. Restaurer la scope parent après (gérer proprement le `ContextVar` token, comme `visit()` le fait déjà).

> Note d'implémentation : `visit()` réinitialise déjà `builder_ctx` par nœud. La scope de `repeat` est un push/pop supplémentaire autour de la boucle interne.

### 4.3 Handlers dans une répétition

Le handler nommé reçoit l'**item de la scope courante** en plus de l'événement. Proposition de contrat :

```python
# signature handler dans un contexte répété
def justify(item, event=None): ...
```

Le builder, en bindant l'event sous une scope `repeat`, enveloppe :
```python
component.on_click(lambda e, it=item: handler(it, e))
```
→ **élimine l'idiome piège** `on_click=lambda _, e=entry: _split(e)` (capture tardive de closure). C'est un argument de vente fort.

Détection « suis-je dans une répétition » : présence de `$key`/`as_name` dans la scope, ou un flag runtime poussé par `repeat`.

### 4.4 Refs sous `repeat` (piège des noms dupliqués)

Les refs nues déclencheraient le `ValueError` de duplication. Deux modes, au choix de conception (je recommande A) :

- **A (recommandé)** : collecter les refs répétées dans un **dict keyé par `key`** :
  `handle.component_refs["justify_btn"]` devient `{seg_id: <button>, …}`.
  Implémentation : si la ref est posée sous une scope `repeat`, stocker dans un sous-dict au lieu d'une valeur scalaire ; erreur si `key` absent.
- **B** : interdire les refs nues sous `repeat` (erreur de build explicite).

### 4.5 Primitive de re-rendu (le fork d'architecture)

`repeat` rend **une fois** au build (cohérent one-shot). Pour les listes vivantes (re-signées sur timer comme la queue downtime), exposer :

```python
handle.rebuild(ref_name: str, *, context: dict | None = None) -> None
```

Sémantique :
1. Localiser le composant `ref_name` (un conteneur, ex. la `column` cible).
2. `component.clear()`.
3. Re-visiter son **template d'enfants d'origine** (conservé à la construction) sous un `ctx` = base + `context` fourni.

> Cela calque exactement le `box.clear()` + repaint qu'on écrit à la main aujourd'hui, **mais garde le template déclaratif**. Pas de diffing, pas d'observers, pas de réactivité implicite.

Pré-requis d'implémentation : `builder` doit **mémoriser, par ref de conteneur, le sous-arbre de layout d'origine** (les nœuds non résolus) pour pouvoir le rejouer. Stocker dans le runtime : `runtime["templates"][ref_name] = original_children`.

### 4.6 Garde-fou : `Live*Binding`

Les `LiveBinding`/`LiveButtonBinding`/… exportés mènent vers un moteur de réactivité qui **chevauche le `.bind_*` natif de NiceGUI**. Recommandation : garder cette couche **mince et optionnelle**, déléguer au binding natif. Ne pas la coupler à `repeat`/`rebuild`.

### 4.7 Cas de test

- `repeat` sur liste de 0, 1, N items → bon nombre d'enfants.
- Scope : `{{ seg.x }}` résout l'item courant ; `$index`/`$key` disponibles.
- Handler répété reçoit le bon item (test anti-capture-tardive).
- Refs mode A : dict keyé correct ; `key` manquant → erreur.
- `rebuild(ref, context=...)` : vide + re-rend avec nouvelles données ; idempotent ; n'affecte pas les autres sous-arbres.

---

## 5. Changements à `visit()` (vue d'ensemble)

Pseudo-code de la boucle par nœud (ajouts en **gras**) :

```
pour chaque nœud:
    ctx = copie(builder_ctx); token = set(ctx)
    normalized = _normalize_layout_entry(nœud, ctx)

    SI normalized est un repeat:                         # §4
        iterable = resolve("{{ in }}")
        runtime["templates"][ref?] = children            # pour rebuild §4.5
        pour i, item dans enumerate(iterable):
            scope = ctx + {as: item, $index: i, $key: resolve(key)}
            avec set(scope): visit(children)             # push/pop scope
        continue

    params  = {k: resolve(v, ctx) for k,v in normalized.params}   # §3 interpolation
    classes = resolve(normalized.classes, ctx)
    props   = resolve(normalized.props, ctx)
    comp = _render_method_chain(normalized.methods, params)
    si classes: comp.classes(classes)
    si props: comp.props(props)

    POUR event, name DANS normalized.on:                 # §2 handlers
        bind_event(comp, event, runtime["handlers"], name, scope_item?)

    si normalized.ref: enregistrer (scalaire ou dict-par-key si sous repeat)  # §4.4
    si normalized.children: avec comp: visit(children)
    set_root_component(ctx, comp); reset(token)
```

`resolve(...)` = nouveau moteur d'interpolation `{{ }}` (§3), avec fallback `_`/`$` déprécié.

`LayoutNode` (models.py) gagne les champs optionnels : `on: dict`, et le type `repeat` (soit un `LayoutNode` spécial, soit un type de nœud distinct reconnu en amont de `_normalize_layout_entry`).

---

## 6. Ordre de livraison recommandé (valeur / effort)

1. **Registre de handlers (`on:`)** — petit, débloque tout le câblage, zéro impact sur l'existant.
2. **Interpolation `{{ }}` typée + filtres** — remplace les sigils fragiles ; prévoir la dépréciation `_`/`$`.
3. **`repeat` + `rebuild(ref, context)`** — le gros morceau ; c'est lui qui relève le plafond constaté (listes/timelines data-driven aujourd'hui forcément impératives).

Chaque étape est indépendante et rétrocompatible ; livrable et testable seule.

---

## 7. Décisions ouvertes (à trancher par l'auteur)

- **Échappement `{{ }}`** : syntaxe retenue (`{{ '{{' }}` vs `\{{`).
- **Refs sous `repeat`** : mode A (dict keyé) vs B (interdit). Reco : A.
- **Contrat de signature handler répété** : `handler(item, event)` vs `handler(event, item=…)` vs introspection. Reco : positionnel `(item, event=None)`.
- **Sort de `$mod:func`** : conserver comme échappatoire avancée, ou déprécier au profit de `filters`/`handlers`.
- **`Live*Binding`** : figer le périmètre (mince + délégué au natif) avant d'ajouter `repeat`.
```
