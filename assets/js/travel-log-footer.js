(function () {
  "use strict";

  var form = document.querySelector("[data-leave-note-form]");
  if (!form || typeof window.formspree !== "function") {
    return;
  }

  var formId = form.getAttribute("data-formspree-id");
  if (!formId) {
    return;
  }

  var submitButton = form.querySelector("[data-fs-submit-btn]");
  var idleButtonText = submitButton ? submitButton.textContent : "Send";

  try {
    window.formspree("initForm", {
      formElement: form,
      formId: formId,
      useDefaultStyles: false,
      disable: function (context) {
        context.form.setAttribute("aria-busy", "true");
        if (submitButton) {
          submitButton.disabled = true;
          submitButton.textContent = "Sending\u2026";
        }
      },
      enable: function (context) {
        context.form.removeAttribute("aria-busy");
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = idleButtonText;
        }
      },
      onSuccess: function (context) {
        context.form.reset();
      }
    });
    form.setAttribute("data-formspree-ready", "true");
  } catch (error) {
    form.removeAttribute("data-formspree-ready");
  }
})();
