var hostEl = document.querySelector("#hosts");
var hostChoices = new Choices(hostEl, {removeItems: true, removeItemButton: true});
function mapHostChoice(value, idx, el) {
  return {value: value, label: value}
}
function setChoices(hosts, finding_name_id, current_status) {
  mapped = hosts.map(mapHostChoice);
  hostChoices.setChoices(mapped, "value", "label", true);

  fm = document.querySelector("#fn_name_action_id")
  fm.setAttribute("value", `${finding_name_id}`)

  fn_status = document.querySelector("#current_status")
  fm_status.setAttribute("value", `${current_status}`)
}

var statusChoiceEl = document.querySelector("#status-choices");
var statusChoices = new Choices(statusChoiceEl, {
  removeItems: true,
  removeItemButton: true
});

var labelChoiceEl = document.querySelector("#label-choices");
var labelChoices = new Choices(labelChoiceEl, {
  removeItems: true,
  removeItemButton: true
});

var severityChoiceEl = document.querySelector("#severity-choices");
var severityChoices = new Choices(severityChoiceEl, {
  removeItems: true,
  removeItemButton: true
});

var assetsChoiceEl = document.querySelector("#assets-choices");
var assetsChoices = new Choices(assetsChoiceEl, {
  removeItems: true,
  removeItemButton: true
});

var sourceChoiceEl = document.querySelector("#source-choices");
var sourceChoices = new Choices(sourceChoiceEl, {
  removeItems: true,
  removeItemButton: true
});

var chLists = [statusChoices, severityChoices, assetsChoices, sourceChoices, labelChoices];

function clearChoices() {
  chLists.forEach(clearChoiceMap);
}

function clearChoiceMap(value, idx, array) {
  value.removeActiveItems();
}
