# CP1 - Inspeção real via MCP `codesys-ide` (2026-11-11)

Chamadas de ferramenta executadas (resultado observado):
- get_active_app_as_path -> `Device.Plc Logic.Application`
- browse_project_tree -> Device > Plc Logic > Application > { PLC_PRG, Task Configuration > MainTask > PLC_PRG }
- get_structured_text_content(PLC_PRG) -> POU **gráfico** (LD/FBD/SFC/CFC), vazio: sem VAR, sem redes.
  Apenas `{attribute 'message_guid'}`. O MCP devolve parse tree somente leitura.
- get_libraries_referenced_in_application -> IoStandard, 3SLicense, CAA Device Diagnosis, Standard, BPLog
- get_device_and_io_configuration -> CODESYS Control Win V3 x64; sem canais de E/S.
- check_for_errors(compile=false) e (compile=true), projeto inteiro -> sem diagnósticos (nenhum erro/aviso).

Ferramentas MCP expostas (20): add_or_remove_library, add_or_remove_program_call_in_task, browse_project_tree,
check_for_errors, create_folder, create_or_replace_structured_text_object, get_active_app_as_path,
get_active_path_and_selection, get_available_libraries_list, get_detailed_library_documentation,
get_device_and_io_configuration, get_libraries_referenced_in_application, get_library_documentation,
get_structured_text_content, remove_object, rename_object, replace_text_in_structured_text,
search_in_files_by_regex, search_libraries_for_type, search_path_by_glob.

Conclusão: **nenhuma ferramenta cria/edita redes LD gráficas**. Criação de LD exige caminho complementar
(importação PLCopen XML / Scripting API). Não se executou download ao runtime nem nada foi modificado.
