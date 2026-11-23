let submittedForm;
const status = document.querySelector("#form-progress");

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || form.method !== "post" || event.defaultPrevented) return;
  if (submittedForm) {
    event.preventDefault();
    return;
  }
  submittedForm = form;
  form.setAttribute("aria-busy", "true");
  status.textContent = "Submitting…";
});

window.addEventListener("pageshow", () => {
  submittedForm?.removeAttribute("aria-busy");
  submittedForm = null;
  status.textContent = "";
});
