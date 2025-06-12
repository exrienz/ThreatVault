const Swal2 = Swal.mixin({
  customClass: {
    input: "form-control",
  },
});

const Toast = Swal.mixin({
  toast: true,
  position: "top-end",
  showConfirmButton: false,
  timer: 3000,
  timerProgressBar: true,
  didOpen: (toast) => {
    toast.addEventListener("mouseenter", Swal.stopTimer);
    toast.addEventListener("mouseleave", Swal.resumeTimer);
  },
});

function ToastSuccessCustom(msg) {
  Toast.fire({
    icon: "success",
    title: msg,
  });
}

function ToastCustom(msg, icon) {
  Toast.fire({
    icon: icon,
    title: msg,
  });
}

function SweetAlert(title, msg, icon) {
  Swal.fire({
    icon: icon,
    title: title,
    text: msg,
    timer: 3500,
  });
}
