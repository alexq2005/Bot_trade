"""
Script para integrar mejoras en el dashboard
Agrega health monitor y visualizaciones mejoradas
"""
import re
from pathlib import Path

dashboard_file = Path("dashboard.py")

if not dashboard_file.exists():
    print("❌ dashboard.py no encontrado")
    exit(1)

# Leer el archivo
with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya tiene las mejoras
if "from src.services.health_monitor import" in content:
    print("✅ Health Monitor ya está integrado")
else:
    # Agregar import después de otros imports
    import_pattern = r"(from src\.services\.[^\n]+\n)"
    health_import = "from src.services.health_monitor import check_system_health\n"
    
    if re.search(import_pattern, content):
        content = re.sub(
            import_pattern,
            r"\1" + health_import,
            content,
            count=1
        )
        print("✅ Health Monitor import agregado")
    else:
        # Agregar al final de los imports
        content = content.replace(
            "from src.services.daily_report_service import DailyReportService",
            "from src.services.daily_report_service import DailyReportService\nfrom src.services.health_monitor import check_system_health"
        )
        print("✅ Health Monitor import agregado")

# Agregar sección de health monitor en la página de sistema
if "### 🏥 Estado del Sistema" not in content:
    # Buscar la sección de Sistema & Configuración
    system_section = "elif page == \"⚙️ Sistema & Configuración\":"
    
    if system_section in content:
        # Agregar tab de health después de los tabs existentes
        tab_pattern = r'(tab_train, tab_growth, tab_risk, tab_sentiment, tab_telegram, tab_reports, tab_logs)'
        if re.search(tab_pattern, content):
            content = re.sub(
                tab_pattern,
                r'tab_train, tab_growth, tab_risk, tab_sentiment, tab_telegram, tab_reports, tab_logs, tab_health',
                content
            )
            
            # Agregar el tab
            tab_health_code = '''
    # --- TAB: HEALTH MONITOR ---
    with tab_health:
        st.subheader("🏥 Monitoreo de Salud del Sistema")
        st.info("💡 Verifica el estado de todos los componentes del sistema")
        
        if st.button("🔄 Verificar Salud", type="primary"):
            with st.spinner("Verificando componentes..."):
                try:
                    health = check_system_health()
                    
                    # Estado general
                    status_colors = {
                        "healthy": "🟢",
                        "degraded": "🟡",
                        "unhealthy": "🔴"
                    }
                    status_icon = status_colors.get(health.overall_status, "⚪")
                    
                    st.markdown(f"### {status_icon} Estado General: {health.overall_status.upper()}")
                    
                    # Componentes
                    st.markdown("### Componentes")
                    for component in health.components:
                        icon = "✅" if component.status == "healthy" else "⚠️" if component.status == "degraded" else "❌"
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.write(f"{icon} **{component.component}**")
                        with col2:
                            st.write(component.message)
                            if component.response_time_ms:
                                st.caption(f"Tiempo de respuesta: {component.response_time_ms:.2f} ms")
                    
                    # Métricas
                    st.markdown("### Métricas")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Componentes Saludables", health.metrics.get('healthy_components', 0))
                    with col2:
                        st.metric("Componentes Degradados", health.metrics.get('degraded_components', 0))
                    with col3:
                        st.metric("Tiempo Total", f"{health.metrics.get('total_check_time_ms', 0):.0f} ms")
                    
                    # Recomendaciones
                    if health.recommendations:
                        st.markdown("### Recomendaciones")
                        for rec in health.recommendations:
                            st.info(rec)
                except Exception as e:
                    st.error(f"Error verificando salud: {e}")
'''
            
            # Insertar después del último tab
            insert_point = content.find("with tab_logs:")
            if insert_point > 0:
                # Encontrar el final del bloque tab_logs
                lines = content[insert_point:].split('\n')
                tab_end = 0
                indent_level = None
                for i, line in enumerate(lines):
                    if i == 0:
                        # Obtener nivel de indentación del tab
                        indent_level = len(line) - len(line.lstrip())
                    if i > 0 and line.strip() and not line.strip().startswith('#'):
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= indent_level and not line.strip().startswith('with tab_'):
                            tab_end = insert_point + sum(len(l) + 1 for l in lines[:i])
                            break
                
                if tab_end > 0:
                    content = content[:tab_end] + tab_health_code + content[tab_end:]
                    print("✅ Tab de Health Monitor agregado")
                else:
                    print("⚠️  No se pudo encontrar el punto de inserción para el tab")
            else:
                print("⚠️  No se encontró la sección de tabs")
        else:
            print("⚠️  No se encontró la sección de Sistema & Configuración")

# Guardar
with open(dashboard_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Mejoras integradas en dashboard.py")
print("💡 Recarga el dashboard para ver los cambios")

