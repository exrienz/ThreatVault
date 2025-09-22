// Filepond: Basic
FilePond.create(document.querySelector(".basic-filepond"), {
  credits: null,
  allowImagePreview: false,
  allowMultiple: false,
  allowFileEncode: false,
  required: false,
})

// Filepond: Multiple Files
FilePond.create(document.querySelector(".multiple-files-filepond"), {
  credits: null,
  allowImagePreview: false,
  allowMultiple: true,
  allowFileEncode: false,
  required: true,
})

// Filepond: With Validation
FilePond.create(document.querySelector(".with-validation-filepond"), {
  credits: null,
  allowImagePreview: false,
  allowMultiple: true,
  allowFileEncode: false,
  required: true,
  acceptedFileTypes: ["image/png"],
  fileValidateTypeDetectType: (source, type) =>
    new Promise((resolve, reject) => {
      // Do custom type detection here and return with promise
      resolve(type)
    }),
})
