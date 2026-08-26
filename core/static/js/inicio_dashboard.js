document.addEventListener("DOMContentLoaded", function () {


    /* ==================================
       MOSTRAR / OCULTAR FORMULARIOS
    ================================== */

    function toggleFormulario(id) {

        const formulario = document.getElementById(id);

        if (!formulario) return;

        formulario.classList.toggle("hidden");

    }


    window.mostrarNota = function () {
        toggleFormulario("formNota");
    }


    window.mostrarPostit = function () {
        toggleFormulario("formPostit");
    }


    window.mostrarIdea = function () {
        toggleFormulario("formIdea");
    }


    window.mostrarEvento = function () {
        toggleFormulario("formEvento");
    }


    window.mostrarRecordatorio = function () {
        toggleFormulario("formRecordatorio");
    }





    /* ==================================
       FULLCALENDAR
    ================================== */


    const calendario = document.getElementById("calendar");


    if (calendario) {


        let eventos = [];


        const datos = document.getElementById("eventos-data");


        if (datos) {

            try {

                eventos = JSON.parse(datos.textContent);

            } catch (error) {

                console.error(
                    "Error cargando eventos:",
                    error
                );

            }

        }



        const calendar = new FullCalendar.Calendar(
            calendario,
            {

                initialView: "dayGridMonth",


                locale: "es",


                height: "auto",


                contentHeight: 500,


                headerToolbar: {

                    left: "prev,next today",

                    center: "title",

                    right: "dayGridMonth,timeGridWeek"

                },


                buttonText: {

                    today: "Hoy",

                    month: "Mes",

                    week: "Semana"

                },


                events: eventos,


                dateClick: function (info) {


                    const fecha =
                        document.querySelector(
                            '#formEvento input[name="fecha"]'
                        );


                    if (fecha) {

                        fecha.value =
                            info.dateStr;

                    }


                    mostrarEvento();


                }


            }

        );


        calendar.render();


    }






    /* ==================================
       BARRA DE PROGRESO
    ================================== */


    const tareas =
        document.querySelectorAll(
            ".nota-item"
        );


    const completadas =
        document.querySelectorAll(
            ".nota-item.completed"
        );


    const barra =
        document.querySelector(
            ".progress-fill"
        );


    if (barra) {


        let porcentaje = 0;


        if (tareas.length > 0) {

            porcentaje =
                (
                    completadas.length /
                    tareas.length
                ) * 100;

        }


        barra.style.width =
            porcentaje + "%";

    }






    /* ==================================
       ANIMACIÓN CARDS
    ================================== */


    const cards =
        document.querySelectorAll(
            ".card, .stat-card"
        );


    cards.forEach(card => {


        card.style.opacity = "0";


        card.style.transform =
            "translateY(20px)";



        setTimeout(() => {


            card.style.transition =
                "all .4s ease";


            card.style.opacity = "1";


            card.style.transform =
                "translateY(0)";


        }, 100);



    });




});
function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {

        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {

            const cookie = cookies[i].trim();

            if (
                cookie.substring(
                    0,
                    name.length + 1
                ) === (name + '=')
            ) {

                cookieValue = decodeURIComponent(
                    cookie.substring(
                        name.length + 1
                    )
                );

                break;

            }

        }

    }

    return cookieValue;

}

const csrftoken = getCookie('csrftoken');
function editarNota(id, texto) {

    Swal.fire({
        title: 'Editar tarea',
        input: 'text',
        inputValue: texto,
        showCancelButton: true,
        confirmButtonText: 'Guardar'
    }).then((result) => {

        if (result.isConfirmed) {

            const form = document.createElement('form');

            form.method = 'POST';
            form.action = `/editar-nota/${id}/`;

            form.innerHTML = `
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="${csrftoken}">

                <input type="hidden"
                       name="texto"
                       value="${result.value}">
            `;

            document.body.appendChild(form);
            form.submit();

        }

    });

}
function editarRecordatorio(id, titulo, fecha, prioridad){

    Swal.fire({
        title:'Editar recordatorio',
        html:`
            <input
                id="tituloRecordatorio"
                class="swal2-input"
                value="${titulo}">

            <input
                id="fechaRecordatorio"
                type="date"
                class="swal2-input"
                value="${fecha}">

            <select
                id="prioridadRecordatorio"
                class="swal2-input">

                <option value="baja" ${prioridad === 'baja' ? 'selected' : ''}>
                    Baja
                </option>

                <option value="media" ${prioridad === 'media' ? 'selected' : ''}>
                    Media
                </option>

                <option value="alta" ${prioridad === 'alta' ? 'selected' : ''}>
                    Alta
                </option>

            </select>
        `,
        showCancelButton:true,
        confirmButtonText:'Guardar'
    }).then((result)=>{

        if(result.isConfirmed){

            const form = document.createElement('form');

            form.method='POST';
            form.action=`/editar-recordatorio/${id}/`;

            form.innerHTML=`
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="${csrftoken}">

                <input type="hidden"
                       name="titulo"
                       value="${document.getElementById('tituloRecordatorio').value}">

                <input type="hidden"
                       name="fecha"
                       value="${document.getElementById('fechaRecordatorio').value}">

                <input type="hidden"
                       name="prioridad"
                       value="${document.getElementById('prioridadRecordatorio').value}">
            `;

            document.body.appendChild(form);
            form.submit();
        }
    });
}
function editarPostit(id, contenido) {

    Swal.fire({
        title: 'Editar nota',
        input: 'textarea',
        inputValue: contenido,
        showCancelButton: true,
        confirmButtonText: 'Guardar'
    }).then((result) => {

        if (result.isConfirmed) {

            const form = document.createElement('form');

            form.method = 'POST';
            form.action = `/editar-postit/${id}/`;

            form.innerHTML = `
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="${csrftoken}">

                <input type="hidden"
                       name="contenido"
                       value="${result.value}">

                <input type="hidden"
                       name="color"
                       value="rosa">
            `;

            document.body.appendChild(form);
            form.submit();

        }

    });

}



function editarIdea(id, titulo, descripcion, categoria){

    Swal.fire({
        title:'Editar idea',
        html:`
            <input
                id="tituloIdea"
                class="swal2-input"
                value="${titulo}">

            <textarea
                id="descIdea"
                class="swal2-textarea">${descripcion}</textarea>

            <select
                id="categoriaIdea"
                class="swal2-input">

                <option value="galeria" ${categoria === 'galeria' ? 'selected' : ''}>Galería</option>
                <option value="post" ${categoria === 'post' ? 'selected' : ''}>Post</option>
                <option value="historia" ${categoria === 'historia' ? 'selected' : ''}>Historia</option>
                <option value="blog" ${categoria === 'blog' ? 'selected' : ''}>Blog</option>
                <option value="otro" ${categoria === 'otro' ? 'selected' : ''}>Otro</option>

            </select>
        `,
        showCancelButton:true,
        confirmButtonText:'Guardar'
    }).then((result)=>{

        if(result.isConfirmed){

            const form=document.createElement('form');

            form.method='POST';
            form.action=`/editar-idea/${id}/`;

            form.innerHTML=`
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="${csrftoken}">

                <input type="hidden"
                       name="titulo"
                       value="${document.getElementById('tituloIdea').value}">

                <input type="hidden"
                       name="descripcion"
                       value="${document.getElementById('descIdea').value}">

                <input type="hidden"
                       name="categoria"
                       value="${document.getElementById('categoriaIdea').value}">
            `;

            document.body.appendChild(form);
            form.submit();
        }
    });
}



function editarEvento(id,titulo,descripcion,fecha,hora,tipo){

    Swal.fire({
        title:'Editar evento',
        html:`
            <input
                id="tituloEvento"
                class="swal2-input"
                value="${titulo}">

            <textarea
                id="descEvento"
                class="swal2-textarea">${descripcion}</textarea>

            <input
                id="fechaEvento"
                type="date"
                class="swal2-input"
                value="${fecha}">

            <input
                id="horaEvento"
                type="time"
                class="swal2-input"
                value="${hora || ''}">

            <select
                id="tipoEvento"
                class="swal2-input">

                <option value="contenido" ${tipo === 'contenido' ? 'selected' : ''}>
                    Contenido
                </option>

                <option value="pedido" ${tipo === 'pedido' ? 'selected' : ''}>
                    Pedido
                </option>

                <option value="reunion" ${tipo === 'reunion' ? 'selected' : ''}>
                    Reunión
                </option>

                <option value="otro" ${tipo === 'otro' ? 'selected' : ''}>
                    Otro
                </option>

            </select>
        `,
        showCancelButton:true,
        confirmButtonText:'Guardar'
    }).then((result)=>{

        if(result.isConfirmed){

            const form=document.createElement('form');

            form.method='POST';
            form.action=`/editar-evento/${id}/`;

            form.innerHTML=`
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="${csrftoken}">

                <input type="hidden"
                       name="titulo"
                       value="${document.getElementById('tituloEvento').value}">

                <input type="hidden"
                       name="descripcion"
                       value="${document.getElementById('descEvento').value}">

                <input type="hidden"
                       name="fecha"
                       value="${document.getElementById('fechaEvento').value}">

                <input type="hidden"
                       name="hora"
                       value="${document.getElementById('horaEvento').value}">

                <input type="hidden"
                       name="tipo"
                       value="${document.getElementById('tipoEvento').value}">
            `;

            document.body.appendChild(form);
            form.submit();
        }
    });
}
function confirmarEstado(e, enlace) {

    e.preventDefault();

    Swal.fire({
        title: '¿Cambiar estado?',
        text: 'Se actualizará la tarea.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí',
        cancelButtonText: 'Cancelar'
    }).then((result) => {

        if (result.isConfirmed) {

            window.location.href = enlace.href;

        }

    });

    return false;
}