const STORAGE_KEY = "novel_knowledge_system_state";
const DATABASE_SETTINGS_KEY = "novel_knowledge_system_database_settings";

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "")
    .replace(/^_+|_+$/g, "");
}

function normalizeText(value) {
  return value.trim().replace(/\s+/g, " ");
}

function makeId(prefix, value) {
  const base = slugify(value) || prefix;
  return `${prefix}_${base}_${Math.random().toString(36).slice(2, 8)}`;
}

function createInitialState() {
  const defaultNovelId = makeId("novel", "default");
  return {
    activeNovelId: defaultNovelId,
    novels: [
      {
        id: defaultNovelId,
        name: "default",
        characters: [],
        plans: [],
        relationships: [],
        customTables: [],
        createdAt: Date.now()
      }
    ]
  };
}

async function getRawState() {
  const result = await chrome.storage.local.get(STORAGE_KEY);
  return result[STORAGE_KEY] || createInitialState();
}

async function saveRawState(state) {
  await chrome.storage.local.set({ [STORAGE_KEY]: state });
  return state;
}

async function getDatabaseSettings() {
  const result = await chrome.storage.local.get(DATABASE_SETTINGS_KEY);
  return result[DATABASE_SETTINGS_KEY] || {
    databaseName: "",
    login: "",
    password: ""
  };
}

async function saveDatabaseSettings(databaseName, login, password) {
  const settings = {
    databaseName: normalizeText(databaseName),
    login: normalizeText(login),
    password: password.trim()
  };
  await chrome.storage.local.set({ [DATABASE_SETTINGS_KEY]: settings });
  return settings;
}

function escapeSqlString(value) {
  return String(value).replace(/'/g, "''");
}

function toSqlValue(value) {
  if (value === null || value === undefined) {
    return "NULL";
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : "NULL";
  }
  return `'${escapeSqlString(value)}'`;
}

function makeInsert(tableName, columns, values) {
  return `INSERT INTO ${tableName} (${columns.join(", ")}) VALUES (${values
    .map((value) => toSqlValue(value))
    .join(", ")});`;
}

function getNovelById(state, novelId) {
  return state.novels.find((novel) => novel.id === novelId) || null;
}

function getActiveNovel(state) {
  return getNovelById(state, state.activeNovelId) || state.novels[0] || null;
}

function ensureActiveNovel(state) {
  if (!state.novels.length) {
    const fresh = createInitialState();
    state.novels = fresh.novels;
    state.activeNovelId = fresh.activeNovelId;
  }
  if (!getNovelById(state, state.activeNovelId)) {
    state.activeNovelId = state.novels[0].id;
  }
  state.novels.forEach((novel) => {
    if (!Array.isArray(novel.characters)) {
      novel.characters = [];
    }
    if (!Array.isArray(novel.plans)) {
      novel.plans = [];
    }
    if (!Array.isArray(novel.relationships)) {
      novel.relationships = [];
    }
    if (!Array.isArray(novel.customTables)) {
      novel.customTables = [];
    }
    novel.characters.forEach((character) => {
      if (!Array.isArray(character.traits)) {
        character.traits = [];
      }
      if (!character.aspects || typeof character.aspects !== "object") {
        character.aspects = {};
      }
    });
    novel.customTables.forEach((table) => {
      if (!Array.isArray(table.values)) {
        table.values = [];
      }
    });
  });
  return state;
}

function sortByName(items) {
  return [...items].sort((a, b) => a.name.localeCompare(b.name));
}

function upsertCharacter(novel, name) {
  const normalized = normalizeText(name);
  const slug = slugify(normalized);
  let character = novel.characters.find((item) => item.slug === slug);
  if (!character) {
    character = {
      id: makeId("character", normalized),
      slug,
      name: normalized,
      description: "",
      traits: [],
      aspects: {},
      createdAt: Date.now()
    };
    novel.characters.push(character);
  }
  return character;
}

function upsertPlan(novel, name, description = "") {
  const normalized = normalizeText(name);
  const slug = slugify(normalized);
  let plan = novel.plans.find((item) => item.slug === slug);
  if (!plan) {
    plan = {
      id: makeId("plan", normalized),
      slug,
      name: normalized,
      description: normalizeText(description),
      createdAt: Date.now()
    };
    novel.plans.push(plan);
  } else if (description.trim()) {
    plan.description = normalizeText(description);
  }
  return plan;
}

function upsertCustomTable(novel, aspectName) {
  const normalized = normalizeText(aspectName);
  const slug = slugify(normalized);
  let table = novel.customTables.find((item) => item.slug === slug);
  if (!table) {
    table = {
      id: makeId("custom_table", normalized),
      slug,
      name: normalized,
      values: [],
      createdAt: Date.now()
    };
    novel.customTables.push(table);
  }
  return table;
}

function getEntityOptions(novel) {
  const characters = novel.characters.map((item) => ({
    id: item.id,
    name: item.name,
    type: "character"
  }));
  const plans = novel.plans.map((item) => ({
    id: item.id,
    name: item.name,
    type: "plan"
  }));
  return sortByName([...characters, ...plans]);
}

function getEntityDisplay(novel, entityId) {
  const character = novel.characters.find((item) => item.id === entityId);
  if (character) {
    return { name: character.name, type: "character" };
  }
  const plan = novel.plans.find((item) => item.id === entityId);
  if (plan) {
    return { name: plan.name, type: "plan" };
  }
  return { name: "unknown", type: "unknown" };
}

async function getState() {
  const state = ensureActiveNovel(await getRawState());
  return saveRawState(state);
}

async function updateState(mutator) {
  const state = ensureActiveNovel(await getRawState());
  mutator(state);
  ensureActiveNovel(state);
  return saveRawState(state);
}

async function createNovel(name) {
  return updateState((state) => {
    const normalized = normalizeText(name);
    const slug = slugify(normalized);
    let novel = state.novels.find((item) => slugify(item.name) === slug);
    if (!novel) {
      novel = {
        id: makeId("novel", normalized),
        name: normalized,
        characters: [],
        plans: [],
        relationships: [],
        customTables: [],
        createdAt: Date.now()
      };
      state.novels.push(novel);
    }
    state.activeNovelId = novel.id;
  });
}

async function selectNovel(novelId) {
  return updateState((state) => {
    if (getNovelById(state, novelId)) {
      state.activeNovelId = novelId;
    }
  });
}

async function deleteNovel(novelId) {
  return updateState((state) => {
    state.novels = state.novels.filter((novel) => novel.id !== novelId);
    if (!state.novels.length) {
      const fresh = createInitialState();
      state.novels = fresh.novels;
      state.activeNovelId = fresh.activeNovelId;
      return;
    }
    if (state.activeNovelId === novelId) {
      state.activeNovelId = state.novels[0].id;
    }
  });
}

async function createCharacter(name) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    upsertCharacter(novel, name);
  });
}

async function deleteCharacter(characterId) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    novel.characters = novel.characters.filter((item) => item.id !== characterId);
    novel.relationships = novel.relationships.filter(
      (item) => item.sourceId !== characterId && item.targetId !== characterId
    );
  });
}

async function addTrait(characterId, trait) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const character = novel.characters.find((item) => item.id === characterId);
    if (!character) return;
    const normalized = normalizeText(trait);
    if (!character.traits.includes(normalized)) {
      character.traits.push(normalized);
      character.traits.sort((a, b) => a.localeCompare(b));
    }
  });
}

async function deleteTrait(characterId, trait) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const character = novel.characters.find((item) => item.id === characterId);
    if (!character) return;
    const normalized = normalizeText(trait);
    character.traits = character.traits.filter((item) => item !== normalized);
  });
}

async function setAspect(characterId, aspectName, aspectValue) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const character = novel.characters.find((item) => item.id === characterId);
    if (!character) return;
    character.aspects[normalizeText(aspectName)] = normalizeText(aspectValue);
  });
}

async function deleteAspect(characterId, aspectName) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const character = novel.characters.find((item) => item.id === characterId);
    if (!character) return;
    delete character.aspects[normalizeText(aspectName)];
  });
}

async function createPlan(name, description) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    upsertPlan(novel, name, description);
  });
}

async function deletePlan(planId) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    novel.plans = novel.plans.filter((item) => item.id !== planId);
    novel.relationships = novel.relationships.filter(
      (item) => item.sourceId !== planId && item.targetId !== planId
    );
  });
}

async function createRelationship(sourceId, targetId, relationType, relationName = "") {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const type = normalizeText(relationType);
    const name = normalizeText(relationName);
    const exists = novel.relationships.find(
      (item) =>
        item.sourceId === sourceId &&
        item.targetId === targetId &&
        item.relationType === type &&
        item.name === name
    );
    if (!exists) {
      novel.relationships.push({
        id: makeId("relationship", `${sourceId}_${targetId}_${type}`),
        sourceId,
        targetId,
        relationType: type,
        name,
        createdAt: Date.now()
      });
    }
  });
}

async function deleteRelationship(relationshipId) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    novel.relationships = novel.relationships.filter((item) => item.id !== relationshipId);
  });
}

async function createCustomTable(aspectName) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    upsertCustomTable(novel, aspectName);
  });
}

async function deleteCustomTable(tableId) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    novel.customTables = novel.customTables.filter((item) => item.id !== tableId);
  });
}

async function addCustomTableValue(tableId, characterId, value) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const table = novel.customTables.find((item) => item.id === tableId);
    if (!table) return;
    table.values.push({
      id: makeId("table_value", value),
      characterId,
      value: normalizeText(value),
      createdAt: Date.now()
    });
  });
}

async function deleteCustomTableValue(tableId, valueId) {
  return updateState((state) => {
    const novel = getActiveNovel(state);
    const table = novel.customTables.find((item) => item.id === tableId);
    if (!table) return;
    table.values = table.values.filter((item) => item.id !== valueId);
  });
}

async function exportState() {
  return getState();
}

async function importState(nextState) {
  const safe = ensureActiveNovel(nextState);
  return saveRawState(safe);
}

async function exportSQLiteDump() {
  const state = await getState();
  const settings = await getDatabaseSettings();
  const lines = [
    "-- Novel Knowledge System SQLite export",
    "PRAGMA foreign_keys = ON;",
    "BEGIN TRANSACTION;",
    "",
    "CREATE TABLE IF NOT EXISTS database_settings (",
    "  id INTEGER PRIMARY KEY CHECK (id = 1),",
    "  database_name TEXT NOT NULL,",
    "  login TEXT NOT NULL,",
    "  password TEXT NOT NULL",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS novels (",
    "  id TEXT PRIMARY KEY,",
    "  name TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  is_active INTEGER NOT NULL DEFAULT 0",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS characters (",
    "  id TEXT PRIMARY KEY,",
    "  novel_id TEXT NOT NULL,",
    "  slug TEXT NOT NULL,",
    "  name TEXT NOT NULL,",
    "  description TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS character_traits (",
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
    "  character_id TEXT NOT NULL,",
    "  trait TEXT NOT NULL,",
    "  FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS character_aspects (",
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
    "  character_id TEXT NOT NULL,",
    "  aspect_name TEXT NOT NULL,",
    "  aspect_value TEXT NOT NULL,",
    "  FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS plans (",
    "  id TEXT PRIMARY KEY,",
    "  novel_id TEXT NOT NULL,",
    "  slug TEXT NOT NULL,",
    "  name TEXT NOT NULL,",
    "  description TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS relationships (",
    "  id TEXT PRIMARY KEY,",
    "  novel_id TEXT NOT NULL,",
    "  source_id TEXT NOT NULL,",
    "  target_id TEXT NOT NULL,",
    "  relation_type TEXT NOT NULL,",
    "  name TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS custom_tables (",
    "  id TEXT PRIMARY KEY,",
    "  novel_id TEXT NOT NULL,",
    "  slug TEXT NOT NULL,",
    "  name TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS custom_table_values (",
    "  id TEXT PRIMARY KEY,",
    "  table_id TEXT NOT NULL,",
    "  character_id TEXT NOT NULL,",
    "  value TEXT NOT NULL,",
    "  created_at INTEGER NOT NULL,",
    "  FOREIGN KEY (table_id) REFERENCES custom_tables(id) ON DELETE CASCADE,",
    "  FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE",
    ");",
    ""
  ];

  lines.push(
    makeInsert(
      "database_settings",
      ["id", "database_name", "login", "password"],
      [1, settings.databaseName || "", settings.login || "", settings.password || ""]
    )
  );

  state.novels.forEach((novel) => {
    lines.push(
      makeInsert(
        "novels",
        ["id", "name", "created_at", "is_active"],
        [novel.id, novel.name, novel.createdAt || 0, novel.id === state.activeNovelId ? 1 : 0]
      )
    );

    novel.characters.forEach((character) => {
      lines.push(
        makeInsert(
          "characters",
          ["id", "novel_id", "slug", "name", "description", "created_at"],
          [
            character.id,
            novel.id,
            character.slug || "",
            character.name,
            character.description || "",
            character.createdAt || 0
          ]
        )
      );

      character.traits.forEach((trait) => {
        lines.push(makeInsert("character_traits", ["character_id", "trait"], [character.id, trait]));
      });

      Object.entries(character.aspects || {}).forEach(([aspectName, aspectValue]) => {
        lines.push(
          makeInsert(
            "character_aspects",
            ["character_id", "aspect_name", "aspect_value"],
            [character.id, aspectName, aspectValue]
          )
        );
      });
    });

    novel.plans.forEach((plan) => {
      lines.push(
        makeInsert(
          "plans",
          ["id", "novel_id", "slug", "name", "description", "created_at"],
          [plan.id, novel.id, plan.slug || "", plan.name, plan.description || "", plan.createdAt || 0]
        )
      );
    });

    novel.relationships.forEach((relationship) => {
      lines.push(
        makeInsert(
          "relationships",
          ["id", "novel_id", "source_id", "target_id", "relation_type", "name", "created_at"],
          [
            relationship.id,
            novel.id,
            relationship.sourceId,
            relationship.targetId,
            relationship.relationType || "",
            relationship.name || "",
            relationship.createdAt || 0
          ]
        )
      );
    });

    novel.customTables.forEach((table) => {
      lines.push(
        makeInsert(
          "custom_tables",
          ["id", "novel_id", "slug", "name", "created_at"],
          [table.id, novel.id, table.slug || "", table.name, table.createdAt || 0]
        )
      );

      table.values.forEach((entry) => {
        lines.push(
          makeInsert(
            "custom_table_values",
            ["id", "table_id", "character_id", "value", "created_at"],
            [entry.id, table.id, entry.characterId, entry.value, entry.createdAt || 0]
          )
        );
      });
    });
  });

  lines.push("", "COMMIT;", "");
  return lines.join("\n");
}

export {
  addCustomTableValue,
  createCharacter,
  createCustomTable,
  createNovel,
  createPlan,
  createRelationship,
  deleteAspect,
  deleteCharacter,
  deleteCustomTable,
  deleteCustomTableValue,
  deleteNovel,
  deletePlan,
  deleteRelationship,
  deleteTrait,
  exportState,
  exportSQLiteDump,
  getActiveNovel,
  getDatabaseSettings,
  getEntityDisplay,
  getEntityOptions,
  getState,
  importState,
  saveDatabaseSettings,
  selectNovel,
  setAspect,
  addTrait,
  deleteTrait as removeTrait
};
