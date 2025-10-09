var labelEl = document.querySelector("#label");

var uploadLabelChoices = new Choices(labelEl, {
  removeItems: true,
  removeItemButton: true,
  maxItemCount: 1,
  addItems: true,
  duplicateItemsAllowed: false,
  searchEnabled: true,
  searchChoices: true,
  shouldSort: false,
  paste: false,
  allowHTML: false,
  noResultsText: 'No results found. Press Enter to add.',
  addItemText: (value) => `Press Enter to add "${value}"`,
});

uploadLabelChoices.input.element.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();

    const value = e.target.value.trim();
    if (!value || value.toLowerCase() === 'select label...') return;

    const selectedValues = uploadLabelChoices.getValue(true);
    const selectedArray = Array.isArray(selectedValues)
      ? selectedValues
      : [selectedValues].filter(Boolean);

    const exists = selectedArray.some(
      v => v.toLowerCase() === value.toLowerCase()
    );
    if (!exists) {
      uploadLabelChoices.setValue([{ value, label: value }]);
    } else {
      uploadLabelChoices.setChoiceByValue(value);
    }
  }
});
