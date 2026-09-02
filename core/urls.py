from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy


urlpatterns = [
    # ==================================================
    # PÁGINAS PÚBLICAS
    # ==================================================
    path('', views.home, name='home'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('contacto/', views.contacto, name='contacto'),
    path('tips/', views.tips, name='tips'),
    path('emprender/', views.emprender, name='emprender'),
    path(
    "terminos-y-condiciones/",
    views.terminos,
    name="terminos"
),

    # ==================================================
    # AUTENTICACIÓN Y REGISTRO
    # ==================================================
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    # ==================================================
# RECUPERACIÓN DE CONTRASEÑA
# ==================================================

path(
    'recuperar-contrasena/',
    auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
        success_url='/recuperar-contrasena/enviado/'
    ),
    name='password_reset'
),

path(
    'recuperar-contrasena/enviado/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ),
    name='password_reset_done'
),

path(
    'recuperar-contrasena/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/recuperar-contrasena/completado/'
    ),
    name='password_reset_confirm'
),

path(
    'recuperar-contrasena/completado/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ),
    name='password_reset_complete'
),
    path('logout/', views.logout_view, name='logout'),
    path('validar-email/', views.validar_email, name='validar_email'),

    # ==================================================
    # PERFIL Y CUENTA DE USUARIO
    # ==================================================
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),

    # ==================================================
    # DASHBOARD Y ADMINISTRACIÓN
    # ==================================================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),

    # ==================================================
    # GESTIÓN DE USUARIOS
    # ==================================================
    path('usuarios/', views.usuario_d, name='usuario_d'),
    path('usuarios/<int:id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('exportar-usuarios-excel/', views.exportar_usuarios_excel, name='exportar_usuarios_excel'),

    # ==================================================
    # GESTIÓN DE DIRECCIONES
    # ==================================================
    path('direcciones/agregar/', views.agregar_direccion, name='agregar_direccion'),
    path('direcciones/eliminar/<int:id>/', views.eliminar_direccion, name='eliminar_direccion'),

    # ==================================================
    # GESTIÓN DEL BLOG
    # ==================================================
    path('blog/', views.blog, name='blog'),
    path('blog-modal/<int:id>/', views.blog_modal, name='blog_modal'),
    path('blog/editar/<int:id>/', views.editar_blog, name='editar_blog'),
    path('blog/publicar/<int:id>/', views.publicar_blog, name='publicar_blog'),
    path('blog/eliminar/<int:id>/', views.eliminar_blog, name='eliminar_blog'),

    # ==================================================
    # GESTIÓN DE GALERÍA
    # ==================================================
    path('galeria/', views.galeria, name='galeria'),
    path('galeria/editar/<int:id>/', views.editar_galeria, name='editar_galeria'),
    path('galeria/eliminar/<int:id>/', views.eliminar_galeria, name='eliminar_galeria'),
    path('galeria-modal/<int:id>/', views.galeria_modal, name='galeria_modal'),

    # ==================================================
    # GESTIÓN DE TESTS
    # ==================================================
    path('test/', views.test, name='test'),
    path('test/<int:test_id>/', views.obtener_test, name='obtener_test'),
    path('test/editar/<int:test_id>/', views.test, name='editar_test'),
    path('test/eliminar/<int:test_id>/', views.eliminar_test, name='eliminar_test'),
    path('test/activar/<int:test_id>/', views.activar_test, name='activar_test'),
    path('test/desactivar/<int:test_id>/', views.desactivar_test, name='desactivar_test'),
    path('resultado/eliminar/<int:resultado_id>/', views.eliminar_resultado_usuario, name='eliminar_resultado_usuario'),
    path('guardar-resultado/', views.guardar_resultado_usuario, name='guardar_resultado_usuario'),

    # ==================================================
    # PRODUCTOS Y CATÁLOGO
    # ==================================================
    path('dashboard/productos/', views.dashboard_productos, name='dashboard_productos'),
    path('dashboard/productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('dashboard/productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('dashboard/catalogo/', views.dashboard_catalogo, name='dashboard_catalogo'),
    path('dashboard/colecciones/', views.obtener_colecciones, name='obtener_colecciones'),
    path('dashboard/catalogo/categoria/<int:id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    path('dashboard/catalogo/marca/<int:id>/eliminar/', views.eliminar_marca, name='eliminar_marca'),
    path('dashboard/catalogo/coleccion/<int:id>/eliminar/', views.eliminar_coleccion, name='eliminar_coleccion'),
    path('dashboard/etiqueta/eliminar/<int:etiqueta_id>/', views.eliminar_etiqueta, name='eliminar_etiqueta'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('catalogo/producto/<slug:slug>/', views.detalle_producto, name='detalle_producto'),

    # ==================================================
    # KITS
    # ==================================================
    path('dashboard/kits/', views.dashboard_kits, name='dashboard_kits'),
    path('dashboard/kits/eliminar/<int:kit_id>/', views.eliminar_kit, name='eliminar_kit'),
    path('dashboard/kits/<int:kit_id>/agregar-producto/', views.agregar_producto_kit, name='agregar_producto_kit'),
    path('dashboard/kits/item/eliminar/<int:item_id>/', views.eliminar_producto_kit, name='eliminar_producto_kit'),
    path('dashboard/kits/toggle/<int:kit_id>/', views.toggle_kit_activo, name='toggle_kit_activo'),
    path('catalogo/kit/<slug:slug>/', views.detalle_kit, name='detalle_kit'),

    # ==================================================
    # GESTIÓN DE CONTACTO
    # ==================================================
    path('dashboard/contacto/', views.dashboard_contacto, name='dashboard_contacto'),
    path('dashboard/contacto/<int:id>/responder/', views.responder_contacto, name='responder_contacto'),
    path('dashboard/contactos/sincronizar/', views.sincronizar_respuestas_gmail, name='sincronizar_respuestas_gmail'),
    path('dashboard/contacto/<int:id>/archivar/', views.archivar_contacto, name='archivar_contacto'),
    path('dashboard/contacto/<int:id>/restaurar/', views.restaurar_contacto, name='restaurar_contacto'),
    path('dashboard/eliminar-mensaje/<int:id>/', views.eliminar_mensaje, name='eliminar_mensaje'),
    path('contacto/marcar-leido/<int:id>/', views.marcar_leido, name='marcar_leido'),

    # ==================================================
    # DASHBOARD - NOTAS CHECKLIST
    # ==================================================
    path('dashboard/nota/<int:id>/eliminar/', views.eliminar_nota, name='eliminar_nota'),
    path('dashboard/nota/<int:id>/toggle/', views.toggle_nota, name='toggle_nota'),
    path('editar-nota/<int:id>/', views.editar_nota, name='editar_nota'),

    # ==================================================
    # DASHBOARD - POST ITS
    # ==================================================
    path('dashboard/postit/<int:id>/eliminar/', views.eliminar_postit, name='eliminar_postit'),
    path('editar-postit/<int:id>/', views.editar_postit, name='editar_postit'),

    # ==================================================
    # DASHBOARD - IDEAS
    # ==================================================
    path('dashboard/idea/<int:id>/editar/', views.editar_idea, name='editar_idea_dashboard'),
    path('dashboard/idea/<int:id>/eliminar/', views.eliminar_idea, name='eliminar_idea'),
    path('dashboard/idea/<int:id>/estado/', views.cambiar_estado_idea, name='cambiar_estado_idea'),
    path('editar-idea/<int:id>/', views.editar_idea, name='editar_idea'),

    # ==================================================
    # DASHBOARD - EVENTOS
    # ==================================================
    path('dashboard/evento/<int:id>/editar/', views.editar_evento, name='editar_evento_dashboard'),
    path('dashboard/evento/<int:id>/eliminar/', views.eliminar_evento, name='eliminar_evento'),
    path('editar-evento/<int:id>/', views.editar_evento, name='editar_evento'),

    # ==================================================
    # DASHBOARD - RECORDATORIOS
    # ==================================================
    path('dashboard/recordatorio/<int:id>/editar/', views.editar_recordatorio, name='editar_recordatorio_dashboard'),
    path('dashboard/recordatorio/<int:id>/eliminar/', views.eliminar_recordatorio, name='eliminar_recordatorio'),
    path('dashboard/recordatorio/<int:id>/toggle/', views.toggle_recordatorio, name='toggle_recordatorio'),
    path('editar-recordatorio/<int:id>/', views.editar_recordatorio, name='editar_recordatorio'),

    # ==================================================
    # CARRITO
    # ==================================================
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:variante_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/aumentar/<int:item_id>/', views.aumentar_carrito, name='aumentar_carrito'),
    path('carrito/disminuir/<int:item_id>/', views.disminuir_carrito, name='disminuir_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/pago/', views.pago_checkout, name='pago_checkout'),
    path('checkout/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('checkout/calcular/', views.calcular_checkout, name='calcular_checkout'),
    path("pedido/<int:pedido_id>/factura/",views.factura_pedido,name="factura_pedido"),
    path("pedidos/",views.dashboard_pedidos,name="dashboard_pedidos"),
    path("pedidos/<int:pedido_id>/",views.dashboard_pedido_detalle,name="dashboard_pedido_detalle"),
    path("pedidos/<int:pedido_id>/estado/",views.dashboard_pedido_estado,name="dashboard_pedido_estado"),
    path("carrito/agregar-kit/<int:kit_id>/", views.agregar_kit_al_carrito, name="agregar_kit_al_carrito"),
    path(
        "dashboard/recomendaciones/",
        views.dashboard_recomendaciones,
        name="dashboard_recomendaciones",
    ),
    path(
        "dashboard/recomendaciones/<int:id>/eliminar/",
        views.eliminar_recomendacion,
        name="eliminar_recomendacion",
    ),
    path(
        "api/recomendar-emprendimiento/",
        views.recomendar_emprendimiento,
        name="recomendar_emprendimiento",
    ),
    path("api/guardar-reporte-emprendimiento/", views.guardar_reporte_emprendimiento, name="guardar_reporte_emprendimiento"),
path("emprender/reportes/<int:id>/", views.reporte_emprendimiento_detalle, name="reporte_emprendimiento_detalle"),
path("emprender/reportes/<int:id>/eliminar/", views.eliminar_reporte_emprendimiento, name="eliminar_reporte_emprendimiento"),

]

# ==================================================
# CONFIGURACIÓN DE ARCHIVOS
# ==================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )