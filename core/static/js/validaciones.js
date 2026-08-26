document.addEventListener("DOMContentLoaded", () => {
    // =========================
    // HELPERS
    // =========================
    const validarEmail = (email) =>
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const validarPassword = (input) => {
        clearError(input);

        const v = input.value;

        if (v.length === 0) {
            return setError(input, "La contraseña es obligatoria");
        }

        if (v.length < 8) {
            return setError(input, "Mínimo 8 caracteres");
        }

        if (!/[A-Z]/.test(v)) {
            return setError(input, "Debe contener una mayúscula");
        }

        if (!/[0-9]/.test(v)) {
            return setError(input, "Debe contener un número");
        }

        return true;
    };

    function setError(input, msg) {
        if (!input || !input.parentElement) return false;

        let error = input.parentElement.querySelector(".error-msg");

        if (!error) {
            error = document.createElement("div");
            error.classList.add("error-msg");
            input.parentElement.appendChild(error);
        }

        error.innerText = msg;
        input.classList.add("input-error");
        return false;
    }

    function clearError(input) {
        if (!input || !input.parentElement) return;

        const error = input.parentElement.querySelector(".error-msg");

        if (error) {
            error.remove();
        }

        input.classList.remove("input-error");
    }

    async function validarEmailUnico(input) {
        clearError(input);

        const v = input.value.trim();
        const original = input.dataset.originalEmail || "";

        if (v.length === 0) {
            return setError(input, "El correo es obligatorio");
        }

        if (v.includes(" ")) {
            return setError(input, "No puede contener espacios");
        }

        if (!validarEmail(v)) {
            return setError(input, "Correo inválido");
        }

        // En perfil, evita consultar si el usuario no cambió su propio correo.
        if (original && v.toLowerCase() === original.toLowerCase()) {
            return true;
        }

        try {
            const res = await fetch(
                `/validar-email/?email=${encodeURIComponent(v)}`
            );

            if (!res.ok) {
                return setError(input, "No se pudo validar el correo");
            }

            const data = await res.json();

            if (data.existe) {
                return setError(input, "Este correo ya está registrado");
            }

            return true;
        } catch (error) {
            return setError(input, "No se pudo validar el correo");
        }
    }

    function setFormMessage(form, text, isError = true) {
        const mensaje =
            form.querySelector(".form-message") ||
            form.querySelector(".form-error");

        if (!mensaje) return;

        mensaje.className = isError
            ? `${mensaje.classList.contains("form-error") ? "form-error" : "form-message"} error`
            : mensaje.classList.contains("form-error")
                ? "form-error"
                : "form-message";

        mensaje.textContent = text;
    }

    function reportarErrores(form, mensaje) {
        const primerError = form.querySelector(".input-error");

        setFormMessage(form, mensaje);

        if (window.Swal) {
            Swal.fire({
                icon: "warning",
                title: "Formulario incompleto",
                text: "Debes llenar todos los campos correctamente antes de continuar.",
                confirmButtonText: "Entendido",
                confirmButtonColor: "#7c3aed"
            });
        } else {
            mostrarAlertaBonitaSinSwal();
        }

        primerError?.focus();
    }

    function mostrarAlertaBonitaSinSwal() {
        const alertaAnterior = document.querySelector(".custom-alert-overlay");

        if (alertaAnterior) {
            alertaAnterior.remove();
        }

        const overlay = document.createElement("div");
        overlay.className = "custom-alert-overlay";
        overlay.innerHTML = `
            <div class="custom-alert">
                <div class="custom-alert-icon">!</div>
                <h2>Formulario incompleto</h2>
                <p>Debes llenar todos los campos correctamente antes de continuar.</p>
                <button type="button">Entendido</button>
            </div>
        `;

        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(15, 23, 42, 0.45);
            padding: 20px;
        `;

        const alerta = overlay.querySelector(".custom-alert");
        alerta.style.cssText = `
            width: min(420px, 100%);
            border-radius: 18px;
            background: #fff;
            padding: 28px;
            text-align: center;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.28);
            font-family: inherit;
        `;

        const icon = overlay.querySelector(".custom-alert-icon");
        icon.style.cssText = `
            width: 58px;
            height: 58px;
            margin: 0 auto 16px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: #fef3c7;
            color: #d97706;
            font-size: 34px;
            font-weight: 800;
        `;

        const title = overlay.querySelector("h2");
        title.style.cssText = `
            margin: 0 0 10px;
            color: #1f2937;
            font-size: 24px;
        `;

        const text = overlay.querySelector("p");
        text.style.cssText = `
            margin: 0 0 22px;
            color: #4b5563;
            line-height: 1.5;
        `;

        const button = overlay.querySelector("button");
        button.style.cssText = `
            border: 0;
            border-radius: 10px;
            background: #7c3aed;
            color: #fff;
            padding: 11px 22px;
            font-weight: 700;
            cursor: pointer;
        `;

        button.addEventListener("click", () => {
            overlay.remove();
        });

        document.body.appendChild(overlay);
    }

    function getPasswordNueva(form) {
        return (
            form.querySelector('input[name="password_nueva"]') ||
            form.querySelector('input[name="password1"]') ||
            form.querySelector('input[name="password"]')
        );
    }

    function getPasswordConfirmar(form) {
        return (
            form.querySelector('input[name="password_confirmar"]') ||
            form.querySelector('input[name="password2"]') ||
            form.querySelector('input[name="password_confirm"]')
        );
    }

    // ==================================================
    // EMAIL UNICO EN TODOS LOS FORMULARIOS
    // ==================================================

    document.querySelectorAll('input[name="email"]').forEach((email) => {
        let timeoutEmail;

        email.addEventListener("input", () => {
            clearTimeout(timeoutEmail);
            clearError(email);

            if (!email.value.trim()) return;

            timeoutEmail = setTimeout(() => {
                validarEmailUnico(email);
            }, 500);
        });
    });

    // ==================================================
    // PERFIL
    // ==================================================

    const perfilForm = document.getElementById("perfilForm");

    if (perfilForm) {
        perfilForm.setAttribute("novalidate", "novalidate");

        const username = perfilForm.querySelector('input[name="username"]');
        const email = perfilForm.querySelector('input[name="email"]');
        const telefono = perfilForm.querySelector('input[name="telefono"]');
        const foto = perfilForm.querySelector('input[name="foto"]');

        if (email && !email.dataset.originalEmail) {
            email.dataset.originalEmail = email.value.trim();
        }

        if (username) {
            username.addEventListener("input", () => {
                clearError(username);

                const v = username.value.trim();

                if (v.length === 0) {
                    return setError(username, "El usuario es obligatorio");
                }

                if (v.includes(" ")) {
                    return setError(username, "No puede contener espacios");
                }

                if (v.length < 3) {
                    return setError(username, "Mínimo 3 caracteres");
                }

                return true;
            });
        }

        if (telefono) {
            telefono.addEventListener("input", () => {
                clearError(telefono);

                telefono.value = telefono.value.replace(/\D/g, "");

                const v = telefono.value;

                if (v.length > 0 && v.length < 10) {
                    return setError(telefono, "Mínimo 10 dígitos");
                }

                if (v.length > 15) {
                    return setError(telefono, "Máximo 15 dígitos");
                }

                return true;
            });
        }

        if (foto) {
            foto.addEventListener("change", () => {
                clearError(foto);

                if (!foto.files.length) return true;

                const file = foto.files[0];
                const tipos = ["image/jpeg", "image/png", "image/webp"];

                if (!tipos.includes(file.type)) {
                    return setError(foto, "Solo JPG, PNG o WEBP");
                }

                if (file.size > 10 * 1024 * 1024) {
                    return setError(foto, "Máximo 10MB");
                }

                return true;
            });
        }

        perfilForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            username?.dispatchEvent(new Event("input"));
            telefono?.dispatchEvent(new Event("input"));
            foto?.dispatchEvent(new Event("change"));

            if (email) {
                await validarEmailUnico(email);
            }

            const errores = perfilForm.querySelectorAll(".input-error");

            if (errores.length > 0) {
                reportarErrores(
                    perfilForm,
                    "Revisa los campos marcados antes de guardar."
                );
                return;
            }

            setFormMessage(perfilForm, "Validación correcta. Enviando...", false);
            perfilForm.submit();
        });
    }

    // ==================================================
    // REGISTRO
    // ==================================================

    const registroForm =
        document.getElementById("registroForm") ||
        document.getElementById("registerForm");

    if (registroForm) {
        registroForm.setAttribute("novalidate", "novalidate");

        const username = registroForm.querySelector('input[name="username"]');
        const email = registroForm.querySelector('input[name="email"]');
        const password = getPasswordNueva(registroForm);
        const confirmar = getPasswordConfirmar(registroForm);

        if (username) {
            username.addEventListener("input", () => {
                clearError(username);

                const v = username.value.trim();

                if (v.length === 0) {
                    return setError(username, "El usuario es obligatorio");
                }

                if (v.includes(" ")) {
                    return setError(username, "No puede contener espacios");
                }

                if (v.length < 3) {
                    return setError(username, "Mínimo 3 caracteres");
                }

                return true;
            });
        }

        if (password) {
            password.addEventListener("input", () => {
                validarPassword(password);

                if (confirmar?.value) {
                    confirmar.dispatchEvent(new Event("input"));
                }
            });
        }

        if (confirmar) {
            confirmar.addEventListener("input", () => {
                clearError(confirmar);

                if (confirmar.value.length === 0) {
                    return setError(confirmar, "Confirma la contraseña");
                }

                if (password && password.value !== confirmar.value) {
                    return setError(confirmar, "Las contraseñas no coinciden");
                }

                return true;
            });
        }

        registroForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            username?.dispatchEvent(new Event("input"));
            password?.dispatchEvent(new Event("input"));
            confirmar?.dispatchEvent(new Event("input"));

            if (email) {
                await validarEmailUnico(email);
            }

            const errores = registroForm.querySelectorAll(".input-error");

            if (errores.length > 0) {
                reportarErrores(
                    registroForm,
                    "Corrige los campos marcados antes de registrarte."
                );
                return;
            }

            setFormMessage(registroForm, "Validación correcta. Enviando...", false);
            registroForm.submit();
        });
    }

    // ==================================================
    // CAMBIAR CONTRASEÑA
    // ==================================================

    const passwordForm = document.getElementById("passwordForm");

    if (passwordForm) {
        passwordForm.setAttribute("novalidate", "novalidate");

        const actual = passwordForm.querySelector(
            'input[name="password_actual"]'
        );
        const nueva = getPasswordNueva(passwordForm);
        const confirmar = getPasswordConfirmar(passwordForm);

        if (actual) {
            actual.addEventListener("input", () => {
                clearError(actual);

                if (!actual.value) {
                    return setError(actual, "La contraseña actual es obligatoria");
                }

                return true;
            });
        }

        if (nueva) {
            nueva.addEventListener("input", () => {
                validarPassword(nueva);

                if (confirmar?.value) {
                    confirmar.dispatchEvent(new Event("input"));
                }
            });
        }

        if (confirmar) {
            confirmar.addEventListener("input", () => {
                clearError(confirmar);

                if (confirmar.value.length === 0) {
                    return setError(confirmar, "Confirma la contraseña");
                }

                if (nueva && nueva.value !== confirmar.value) {
                    return setError(confirmar, "Las contraseñas no coinciden");
                }

                return true;
            });
        }

        passwordForm.addEventListener("submit", (e) => {
            e.preventDefault();

            actual?.dispatchEvent(new Event("input"));
            nueva?.dispatchEvent(new Event("input"));
            confirmar?.dispatchEvent(new Event("input"));

            const errores = passwordForm.querySelectorAll(".input-error");

            if (errores.length > 0) {
                reportarErrores(
                    passwordForm,
                    "Corrige los campos marcados antes de continuar."
                );
                return;
            }

            setFormMessage(passwordForm, "Validación correcta. Enviando...", false);
            passwordForm.submit();
        });
    }

    // ==================================================
    // MOSTRAR / OCULTAR PASSWORD
    // ==================================================

    document.querySelectorAll(".toggle-password").forEach((icon) => {
        icon.addEventListener("click", () => {
            const input = icon.parentElement.querySelector("input");

            if (!input) return;

            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("fa-eye");
                icon.classList.add("fa-eye-slash");
            } else {
                input.type = "password";
                icon.classList.remove("fa-eye-slash");
                icon.classList.add("fa-eye");
            }
        });
    });

    // ==================================================
    // NOTIFICACIONES
    // ==================================================

    document.querySelectorAll(".notification").forEach((notification) => {
        setTimeout(() => {
            notification.style.opacity = "0";
            notification.style.transform = "translateX(100%)";

            setTimeout(() => {
                notification.remove();
            }, 400);
        }, 4000);
    });
});
