import {
  addCustomTableValue,
  addTrait,
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
  exportState,
  getActiveNovel,
  getEntityDisplay,
  getEntityOptions,
  removeTrait,
  selectNovel,
  setAspect
} from "./storage.js";

const state = {
  snapshot: null,
  selectedCharacterId: null,
  selectedPlanId: null,
  selectedTableId: null,
  selectedTableCharacterId: null,
  selectedSourceId: null,
  selectedTargetId: null,
  activeTab: "characters",
  characterSearch: "",
  planSearch: "",
  relationshipSearch: "",
  tableSearch: ""
};

const elements = {
  activeNovelLabel: document.querySelector("#activeNovelLabel"),
  novelForm: document.querySelector("#novelForm"),
  novelNameInput: document.querySelector("#novelNameInput"),
  novelList: document.querySelector("#novelList"),
  tabRow: document.querySelector("#tabRow"),
  charactersTab: document.querySelector("#charactersTab"),
  plansTab: document.querySelector("#plansTab"),
  relationsTab: document.querySelector("#relationsTab"),
  tablesTab: document.querySelector("#tablesTab"),
  characterSearchInput: document.querySelector("#characterSearchInput"),
  characterForm: document.querySelector("#characterForm"),
  characterNameInput: document.querySelector("#characterNameInput"),
  characterList: document.querySelector("#characterList"),
  characterEmpty: document.querySelector("#characterEmpty"),
  characterDetail: document.querySelector("#characterDetail"),
  characterTitle: document.querySelector("#characterTitle"),
  deleteCharacterButton: document.querySelector("#deleteCharacterButton"),
  traitForm: document.querySelector("#traitForm"),
  traitInput: document.querySelector("#traitInput"),
  traitList: document.querySelector("#traitList"),
  aspectForm: document.querySelector("#aspectForm"),
  aspectNameInput: document.querySelector("#aspectNameInput"),
  aspectValueInput: document.querySelector("#aspectValueInput"),
  aspectList: document.querySelector("#aspectList"),
  planSearchInput: document.querySelector("#planSearchInput"),
  planForm: document.querySelector("#planForm"),
  planNameInput: document.querySelector("#planNameInput"),
  planDescriptionInput: document.querySelector("#planDescriptionInput"),
  planList: document.querySelector("#planList"),
  planEmpty: document.querySelector("#planEmpty"),
  planDetail: document.querySelector("#planDetail"),
  planTitle: document.querySelector("#planTitle"),
  planDescription: document.querySelector("#planDescription"),
  deletePlanButton: document.querySelector("#deletePlanButton"),
  sourceSelector: document.querySelector("#sourceSelector"),
  targetSelector: document.querySelector("#targetSelector"),
  relationForm: document.querySelector("#relationForm"),
  relationTypeInput: document.querySelector("#relationTypeInput"),
  relationNameInput: document.querySelector("#relationNameInput"),
  relationshipSearchInput: document.querySelector("#relationshipSearchInput"),
  relationshipList: document.querySelector("#relationshipList"),
  tableSearchInput: document.querySelector("#tableSearchInput"),
  tableForm: document.querySelector("#tableForm"),
  tableNameInput: document.querySelector("#tableNameInput"),
  tableList: document.querySelector("#tableList"),
  tableEmpty: document.querySelector("#tableEmpty"),
  tableDetail: document.querySelector("#tableDetail"),
  tableTitle: document.querySelector("#tableTitle"),
  deleteTableButton: document.querySelector("#deleteTableButton"),
  tableCharacterSelector: document.querySelector("#tableCharacterSelector"),
  tableValueForm: document.querySelector("#tableValueForm"),
  tableValueInput: document.querySelector("#tableValueInput"),
  tableValueList: document.querySelector("#tableValueList"),
  toast: document.querySelector("#toast")
};

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timeoutId);
  showToast.timeoutId = window.setTimeout(() => {
    elements.toast.classList.add("hidden");
  }, 2200);
}

function getNovel() {
  return getActiveNovel(state.snapshot);
}

function normalizeQuery(value) {
  return value.trim().toLowerCase();
}

function matchesQuery(values, query) {
  if (!query) {
    return true;
  }
  return values.some((value) => String(value).toLowerCase().includes(query));
}

function createEmptyMessage(message) {
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.textContent = message;
  return empty;
}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `${tabName}Tab`);
  });
}

function createChip({ label, subtitle, active = false, onClick, danger = false }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `selector-chip${active ? " active" : ""}`;
  if (danger) {
    button.classList.add("danger");
  }
  button.innerHTML = subtitle
    ? `<span class="selector-title">${label}</span><span class="selector-subtitle">${subtitle}</span>`
    : `<span class="selector-title">${label}</span>`;
  button.addEventListener("click", onClick);
  return button;
}

function createMiniDeleteButton(onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "mini-button";
  button.textContent = "Delete";
  button.addEventListener("click", onClick);
  return button;
}

function renderNovels() {
  const novel = getNovel();
  elements.activeNovelLabel.textContent = novel ? `Active: ${novel.name}` : "No active novel";
  elements.novelList.replaceChildren();

  state.snapshot.novels
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .forEach((item) => {
      const wrapper = document.createElement("div");
      wrapper.className = "detail-item";
      const left = document.createElement("div");
      left.innerHTML = `<strong>${item.name}</strong><small>${item.characters.length} characters · ${item.plans.length} plans · ${item.customTables.length} tables</small>`;
      const actions = document.createElement("div");
      actions.className = "pill-list";

      const selectButton = document.createElement("button");
      selectButton.type = "button";
      selectButton.className = item.id === novel.id ? "ghost" : "";
      selectButton.textContent = item.id === novel.id ? "Selected" : "Switch";
      selectButton.disabled = item.id === novel.id;
      selectButton.addEventListener("click", async () => {
        await selectNovel(item.id);
        await refresh();
        showToast(`Switched to ${item.name}`);
      });

      const deleteButton = createMiniDeleteButton(async () => {
        await deleteNovel(item.id);
        await refresh();
        showToast(`Deleted ${item.name}`);
      });

      actions.append(selectButton, deleteButton);
      wrapper.append(left, actions);
      elements.novelList.append(wrapper);
    });
}

function renderCharacters() {
  const novel = getNovel();
  elements.characterList.replaceChildren();
  const query = state.characterSearch;
  const characters = [...novel.characters]
    .sort((a, b) => a.name.localeCompare(b.name))
    .filter((character) =>
      matchesQuery(
        [character.name, character.traits.join(" "), ...Object.keys(character.aspects), ...Object.values(character.aspects)],
        query
      )
    );

  if (!characters.length) {
    elements.characterList.append(
      createEmptyMessage(query ? "No characters match this search." : "No characters yet.")
    );
  }

  characters.forEach((character) => {
    const chip = createChip({
      label: character.name,
      subtitle: `${character.traits.length} traits · ${Object.keys(character.aspects).length} aspects`,
      active: state.selectedCharacterId === character.id,
      onClick: () => {
        state.selectedCharacterId = character.id;
        renderCharacters();
      }
    });
    elements.characterList.append(chip);
  });

  const selected = novel.characters.find((item) => item.id === state.selectedCharacterId) || null;
  elements.deleteCharacterButton.disabled = !selected;
  elements.characterEmpty.classList.toggle("hidden", Boolean(selected));
  elements.characterDetail.classList.toggle("hidden", !selected);

  if (!selected) {
    return;
  }

  elements.characterTitle.textContent = selected.name;
  elements.traitList.replaceChildren();
  if (!selected.traits.length) {
    elements.traitList.append(createEmptyMessage("No traits saved yet."));
  }
  selected.traits.forEach((trait) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = trait;
    pill.append(
      createMiniDeleteButton(async () => {
        await removeTrait(selected.id, trait);
        await refresh();
        showToast(`Removed trait ${trait}`);
      })
    );
    elements.traitList.append(pill);
  });

  elements.aspectList.replaceChildren();
  const aspectEntries = Object.entries(selected.aspects).sort(([left], [right]) => left.localeCompare(right));
  if (!aspectEntries.length) {
    elements.aspectList.append(createEmptyMessage("No aspects saved yet."));
  }
  aspectEntries.forEach(([key, value]) => {
    const row = document.createElement("div");
    row.className = "detail-item";
    const info = document.createElement("div");
    info.innerHTML = `<strong>${key}</strong><small>${value}</small>`;
    row.append(
      info,
      createMiniDeleteButton(async () => {
        await deleteAspect(selected.id, key);
        await refresh();
        showToast(`Deleted aspect ${key}`);
      })
    );
    elements.aspectList.append(row);
  });
}

function renderPlans() {
  const novel = getNovel();
  elements.planList.replaceChildren();
  const query = state.planSearch;
  const plans = [...novel.plans]
    .sort((a, b) => a.name.localeCompare(b.name))
    .filter((plan) => matchesQuery([plan.name, plan.description], query));

  if (!plans.length) {
    elements.planList.append(createEmptyMessage(query ? "No plans match this search." : "No plans yet."));
  }

  plans.forEach((plan) => {
    const chip = createChip({
      label: plan.name,
      subtitle: plan.description || "No description yet",
      active: state.selectedPlanId === plan.id,
      onClick: () => {
        state.selectedPlanId = plan.id;
        renderPlans();
      }
    });
    elements.planList.append(chip);
  });

  const selected = novel.plans.find((item) => item.id === state.selectedPlanId) || null;
  elements.deletePlanButton.disabled = !selected;
  elements.planEmpty.classList.toggle("hidden", Boolean(selected));
  elements.planDetail.classList.toggle("hidden", !selected);

  if (!selected) {
    return;
  }

  elements.planTitle.textContent = selected.name;
  elements.planDescription.textContent = selected.description || "No description yet.";
}

function renderRelationSelectors() {
  const options = getEntityOptions(getNovel());
  elements.sourceSelector.replaceChildren();
  elements.targetSelector.replaceChildren();

  if (!options.length) {
    elements.sourceSelector.append(createEmptyMessage("Create characters or plans first."));
    elements.targetSelector.append(createEmptyMessage("Create characters or plans first."));
    return;
  }

  options.forEach((entity) => {
    const sourceChip = createChip({
      label: entity.name,
      subtitle: entity.type,
      active: state.selectedSourceId === entity.id,
      onClick: () => {
        state.selectedSourceId = entity.id;
        renderRelationSelectors();
      }
    });
    const targetChip = createChip({
      label: entity.name,
      subtitle: entity.type,
      active: state.selectedTargetId === entity.id,
      onClick: () => {
        state.selectedTargetId = entity.id;
        renderRelationSelectors();
      }
    });
    elements.sourceSelector.append(sourceChip);
    elements.targetSelector.append(targetChip);
  });
}

function renderRelationships() {
  const novel = getNovel();
  elements.relationshipList.replaceChildren();
  const query = state.relationshipSearch;
  const relationships = novel.relationships
    .slice()
    .filter((relationship) => {
      const source = getEntityDisplay(novel, relationship.sourceId);
      const target = getEntityDisplay(novel, relationship.targetId);
      return matchesQuery(
        [source.name, source.type, target.name, target.type, relationship.relationType, relationship.name || ""],
        query
      );
    })
    .sort((a, b) => {
      const left = `${a.relationType} ${a.name || ""}`;
      const right = `${b.relationType} ${b.name || ""}`;
      return left.localeCompare(right);
    });

  if (!relationships.length) {
    elements.relationshipList.append(
      createEmptyMessage(query ? "No relationships match this search." : "No relationships yet.")
    );
    return;
  }

  relationships.forEach((relationship) => {
    const source = getEntityDisplay(novel, relationship.sourceId);
    const target = getEntityDisplay(novel, relationship.targetId);
    const row = document.createElement("div");
    row.className = "detail-item";
    const info = document.createElement("div");
    const relationName = relationship.name ? ` · ${relationship.name}` : "";
    info.innerHTML = `<strong>${source.name} → ${target.name}</strong><small>${relationship.relationType}${relationName}</small>`;
    row.append(
      info,
      createMiniDeleteButton(async () => {
        await deleteRelationship(relationship.id);
        await refresh();
        showToast("Relationship deleted");
      })
    );
    elements.relationshipList.append(row);
  });
}

function renderTables() {
  const novel = getNovel();
  elements.tableList.replaceChildren();
  const query = state.tableSearch;
  const tables = [...novel.customTables]
    .sort((a, b) => a.name.localeCompare(b.name))
    .filter((table) => matchesQuery([table.name], query));

  if (!tables.length) {
    elements.tableList.append(
      createEmptyMessage(query ? "No custom tables match this search." : "No custom tables yet.")
    );
  }

  tables.forEach((table) => {
    const chip = createChip({
      label: table.name,
      subtitle: `${table.values.length} stored values`,
      active: state.selectedTableId === table.id,
      onClick: () => {
        state.selectedTableId = table.id;
        state.selectedTableCharacterId = null;
        renderTables();
      }
    });
    elements.tableList.append(chip);
  });

  const selected = novel.customTables.find((item) => item.id === state.selectedTableId) || null;
  elements.deleteTableButton.disabled = !selected;
  elements.tableEmpty.classList.toggle("hidden", Boolean(selected));
  elements.tableDetail.classList.toggle("hidden", !selected);

  if (!selected) {
    return;
  }

  elements.tableTitle.textContent = selected.name;
  elements.tableCharacterSelector.replaceChildren();
  if (!novel.characters.length) {
    elements.tableCharacterSelector.append(
      createEmptyMessage("Create a character before storing table values.")
    );
  } else {
    novel.characters
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((character) => {
        const count = selected.values.filter((item) => item.characterId === character.id).length;
        const chip = createChip({
          label: character.name,
          subtitle: count ? `${count} values` : "No values yet",
          active: state.selectedTableCharacterId === character.id,
          onClick: () => {
            state.selectedTableCharacterId = character.id;
            renderTables();
          }
        });
        elements.tableCharacterSelector.append(chip);
      });
  }

  elements.tableValueList.replaceChildren();
  const matchingValues = selected.values
    .slice()
    .filter((item) => !state.selectedTableCharacterId || item.characterId === state.selectedTableCharacterId)
    .sort((a, b) => a.value.localeCompare(b.value));

  if (!matchingValues.length) {
    const message = state.selectedTableCharacterId
      ? "No values stored for this character yet."
      : "Select a character or add the first value.";
    elements.tableValueList.append(createEmptyMessage(message));
    return;
  }

  matchingValues.forEach((entry) => {
    const owner = novel.characters.find((item) => item.id === entry.characterId);
    const row = document.createElement("div");
    row.className = "detail-item";
    const info = document.createElement("div");
    info.innerHTML = `<strong>${entry.value}</strong><small>${owner?.name || "Unknown character"}</small>`;
    row.append(
      info,
      createMiniDeleteButton(async () => {
        await deleteCustomTableValue(selected.id, entry.id);
        await refresh();
        showToast("Table value deleted");
      })
    );
    elements.tableValueList.append(row);
  });
}

async function refresh() {
  state.snapshot = await exportState();
  const novel = getNovel();

  if (!novel.characters.some((item) => item.id === state.selectedCharacterId)) {
    state.selectedCharacterId = novel.characters[0]?.id || null;
  }
  if (!novel.plans.some((item) => item.id === state.selectedPlanId)) {
    state.selectedPlanId = novel.plans[0]?.id || null;
  }
  if (!novel.customTables.some((item) => item.id === state.selectedTableId)) {
    state.selectedTableId = novel.customTables[0]?.id || null;
  }
  if (!novel.characters.some((item) => item.id === state.selectedTableCharacterId)) {
    state.selectedTableCharacterId = null;
  }
  if (!getEntityOptions(novel).some((item) => item.id === state.selectedSourceId)) {
    state.selectedSourceId = null;
  }
  if (!getEntityOptions(novel).some((item) => item.id === state.selectedTargetId)) {
    state.selectedTargetId = null;
  }

  renderNovels();
  renderCharacters();
  renderPlans();
  renderRelationSelectors();
  renderRelationships();
  renderTables();
  setActiveTab(state.activeTab);
}

elements.tabRow.addEventListener("click", (event) => {
  const button = event.target.closest(".tab-button");
  if (!button) {
    return;
  }
  setActiveTab(button.dataset.tab);
});

elements.characterSearchInput.addEventListener("input", (event) => {
  state.characterSearch = normalizeQuery(event.target.value);
  renderCharacters();
});

elements.planSearchInput.addEventListener("input", (event) => {
  state.planSearch = normalizeQuery(event.target.value);
  renderPlans();
});

elements.relationshipSearchInput.addEventListener("input", (event) => {
  state.relationshipSearch = normalizeQuery(event.target.value);
  renderRelationships();
});

elements.tableSearchInput.addEventListener("input", (event) => {
  state.tableSearch = normalizeQuery(event.target.value);
  renderTables();
});

elements.novelForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createNovel(elements.novelNameInput.value);
  elements.novelNameInput.value = "";
  await refresh();
  showToast("Novel created");
});

elements.characterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createCharacter(elements.characterNameInput.value);
  elements.characterNameInput.value = "";
  await refresh();
  showToast("Character created");
});

elements.deleteCharacterButton.addEventListener("click", async () => {
  if (!state.selectedCharacterId) {
    return;
  }
  await deleteCharacter(state.selectedCharacterId);
  state.selectedCharacterId = null;
  await refresh();
  showToast("Character deleted");
});

elements.traitForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedCharacterId) {
    return;
  }
  await addTrait(state.selectedCharacterId, elements.traitInput.value);
  elements.traitInput.value = "";
  await refresh();
  showToast("Trait saved");
});

elements.aspectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedCharacterId) {
    return;
  }
  await setAspect(
    state.selectedCharacterId,
    elements.aspectNameInput.value,
    elements.aspectValueInput.value
  );
  elements.aspectNameInput.value = "";
  elements.aspectValueInput.value = "";
  await refresh();
  showToast("Aspect saved");
});

elements.planForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createPlan(elements.planNameInput.value, elements.planDescriptionInput.value);
  elements.planNameInput.value = "";
  elements.planDescriptionInput.value = "";
  await refresh();
  showToast("Plan created");
});

elements.deletePlanButton.addEventListener("click", async () => {
  if (!state.selectedPlanId) {
    return;
  }
  await deletePlan(state.selectedPlanId);
  state.selectedPlanId = null;
  await refresh();
  showToast("Plan deleted");
});

elements.relationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedSourceId || !state.selectedTargetId) {
    showToast("Choose both source and target");
    return;
  }
  await createRelationship(
    state.selectedSourceId,
    state.selectedTargetId,
    elements.relationTypeInput.value,
    elements.relationNameInput.value
  );
  elements.relationTypeInput.value = "";
  elements.relationNameInput.value = "";
  await refresh();
  showToast("Relationship created");
});

elements.tableForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createCustomTable(elements.tableNameInput.value);
  elements.tableNameInput.value = "";
  await refresh();
  showToast("Custom table created");
});

elements.deleteTableButton.addEventListener("click", async () => {
  if (!state.selectedTableId) {
    return;
  }
  await deleteCustomTable(state.selectedTableId);
  state.selectedTableId = null;
  state.selectedTableCharacterId = null;
  await refresh();
  showToast("Custom table deleted");
});

elements.tableValueForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedTableId) {
    showToast("Choose a custom table first");
    return;
  }
  if (!state.selectedTableCharacterId) {
    showToast("Choose a character first");
    return;
  }
  await addCustomTableValue(
    state.selectedTableId,
    state.selectedTableCharacterId,
    elements.tableValueInput.value
  );
  elements.tableValueInput.value = "";
  await refresh();
  showToast("Table value added");
});

refresh();
