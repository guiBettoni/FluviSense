-- 006: todas as tabelas, colunas, restrições, índices e sequências passam a ter nomes em português.
--
-- Por quê: o projeto é brasileiro e o banco precisa ser lido por quem fala português. As migrações
-- 001 a 005 continuam como foram executadas no Supabase (com os nomes da época); esta migração
-- renomeia o resultado delas. Renomear não apaga nem copia dados: as linhas continuam as mesmas.
--
-- As renomeações só acontecem quando o nome antigo existe. Assim, se o banco de produção tiver
-- alguma diferença em relação às migrações (por exemplo, uma tabela antiga criada de outro jeito),
-- a migração não falha: o que não existir é simplesmente pulado.
--
-- Também troca o perfil 'OPERATOR' por 'OPERADOR'. Quem estiver logado precisa entrar de novo.

begin;

create function pg_temp.renomear_tabela(antiga text, nova text) returns void language plpgsql as $$
begin
  if to_regclass('public.' || antiga) is not null and to_regclass('public.' || nova) is null then
    execute format('alter table public.%I rename to %I', antiga, nova);
  end if;
end $$;

create function pg_temp.renomear_coluna(tabela text, antiga text, nova text) returns void language plpgsql as $$
begin
  if exists (select 1 from information_schema.columns
             where table_schema = 'public' and table_name = tabela and column_name = antiga) then
    execute format('alter table public.%I rename column %I to %I', tabela, antiga, nova);
  end if;
end $$;

-- ---------- Tabelas ----------
select pg_temp.renomear_tabela('rivers', 'rios');
select pg_temp.renomear_tabela('monitoring_points', 'pontos_monitoramento');
select pg_temp.renomear_tabela('measurements', 'medicoes');
select pg_temp.renomear_tabela('point_occurrences', 'ocorrencias');
select pg_temp.renomear_tabela('app_users', 'usuarios');
select pg_temp.renomear_tabela('audit_events', 'eventos_auditoria');
-- Tabelas do MVP de 2026.1, que o sistema não usa mais (ficam como registro).
select pg_temp.renomear_tabela('sensors', 'sensores');
select pg_temp.renomear_tabela('sensor_readings', 'leituras_sensores');
select pg_temp.renomear_tabela('residents', 'moradores');
select pg_temp.renomear_tabela('shelters', 'abrigos');
select pg_temp.renomear_tabela('manual_occurrences', 'ocorrencias_manuais');

-- ---------- Colunas ----------
select pg_temp.renomear_coluna('rios', 'name', 'nome');
select pg_temp.renomear_coluna('rios', 'notes', 'observacoes');
select pg_temp.renomear_coluna('rios', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('pontos_monitoramento', 'code', 'codigo');
select pg_temp.renomear_coluna('pontos_monitoramento', 'name', 'nome');
select pg_temp.renomear_coluna('pontos_monitoramento', 'river_id', 'rio_id');
select pg_temp.renomear_coluna('pontos_monitoramento', 'neighborhood', 'bairro');
select pg_temp.renomear_coluna('pontos_monitoramento', 'location_description', 'descricao_local');
select pg_temp.renomear_coluna('pontos_monitoramento', 'attention_distance_cm', 'distancia_atencao_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'alert_distance_cm', 'distancia_alerta_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'critical_distance_cm', 'distancia_critica_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'criteria_provisional', 'criterios_provisorios');
select pg_temp.renomear_coluna('pontos_monitoramento', 'criteria_note', 'justificativa_criterios');
select pg_temp.renomear_coluna('pontos_monitoramento', 'min_valid_distance_cm', 'distancia_minima_valida_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'max_valid_distance_cm', 'distancia_maxima_valida_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'max_jump_cm', 'salto_maximo_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'stale_after_minutes', 'minutos_para_desatualizar');
select pg_temp.renomear_coluna('pontos_monitoramento', 'device_key_hash', 'hash_chave_sensor');
select pg_temp.renomear_coluna('pontos_monitoramento', 'active', 'ativo');
select pg_temp.renomear_coluna('pontos_monitoramento', 'created_at', 'criado_em');
select pg_temp.renomear_coluna('pontos_monitoramento', 'updated_at', 'atualizado_em');

select pg_temp.renomear_coluna('medicoes', 'point_id', 'ponto_id');
select pg_temp.renomear_coluna('medicoes', 'distance_cm', 'distancia_cm');
select pg_temp.renomear_coluna('medicoes', 'unit', 'unidade');
select pg_temp.renomear_coluna('medicoes', 'origin', 'origem');
select pg_temp.renomear_coluna('medicoes', 'measured_at', 'medida_em');
select pg_temp.renomear_coluna('medicoes', 'received_at', 'recebida_em');
select pg_temp.renomear_coluna('medicoes', 'validity', 'validade');
select pg_temp.renomear_coluna('medicoes', 'validity_reason', 'motivo_validade');
select pg_temp.renomear_coluna('medicoes', 'reference_cm', 'referencia_cm');
select pg_temp.renomear_coluna('medicoes', 'classification', 'classificacao');
select pg_temp.renomear_coluna('medicoes', 'created_by', 'registrada_por');

select pg_temp.renomear_coluna('ocorrencias', 'point_id', 'ponto_id');
select pg_temp.renomear_coluna('ocorrencias', 'classification', 'classificacao');
select pg_temp.renomear_coluna('ocorrencias', 'reason', 'motivo');
select pg_temp.renomear_coluna('ocorrencias', 'opened_by', 'aberta_por');
select pg_temp.renomear_coluna('ocorrencias', 'opened_at', 'aberta_em');
select pg_temp.renomear_coluna('ocorrencias', 'closed_at', 'encerrada_em');
select pg_temp.renomear_coluna('ocorrencias', 'closed_by', 'encerrada_por');

select pg_temp.renomear_coluna('usuarios', 'name', 'nome');
select pg_temp.renomear_coluna('usuarios', 'password_hash', 'hash_senha');
select pg_temp.renomear_coluna('usuarios', 'role', 'perfil');
select pg_temp.renomear_coluna('usuarios', 'active', 'ativo');
select pg_temp.renomear_coluna('usuarios', 'last_login_at', 'ultimo_login_em');
select pg_temp.renomear_coluna('usuarios', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('eventos_auditoria', 'actor', 'autor');
select pg_temp.renomear_coluna('eventos_auditoria', 'action', 'acao');
select pg_temp.renomear_coluna('eventos_auditoria', 'entity', 'entidade');
select pg_temp.renomear_coluna('eventos_auditoria', 'details', 'detalhes');
select pg_temp.renomear_coluna('eventos_auditoria', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('sensores', 'sensor_code', 'codigo_sensor');
select pg_temp.renomear_coluna('sensores', 'name', 'nome');
select pg_temp.renomear_coluna('sensores', 'neighborhood', 'bairro');
select pg_temp.renomear_coluna('sensores', 'location_description', 'descricao_local');
select pg_temp.renomear_coluna('sensores', 'threshold_yellow', 'limiar_amarelo');
select pg_temp.renomear_coluna('sensores', 'threshold_orange', 'limiar_laranja');
select pg_temp.renomear_coluna('sensores', 'threshold_red', 'limiar_vermelho');
select pg_temp.renomear_coluna('sensores', 'current_level', 'nivel_atual');
select pg_temp.renomear_coluna('sensores', 'current_status', 'situacao_atual');
select pg_temp.renomear_coluna('sensores', 'active', 'ativo');
select pg_temp.renomear_coluna('sensores', 'last_reading_at', 'ultima_leitura_em');
select pg_temp.renomear_coluna('sensores', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('leituras_sensores', 'water_level_cm', 'nivel_agua_cm');
select pg_temp.renomear_coluna('leituras_sensores', 'origin', 'origem');
select pg_temp.renomear_coluna('leituras_sensores', 'status_generated', 'situacao_gerada');
select pg_temp.renomear_coluna('leituras_sensores', 'is_valid', 'valida');
select pg_temp.renomear_coluna('leituras_sensores', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('moradores', 'name', 'nome');
select pg_temp.renomear_coluna('moradores', 'neighborhood', 'bairro');
select pg_temp.renomear_coluna('moradores', 'street', 'rua');
select pg_temp.renomear_coluna('moradores', 'consent_at', 'consentimento_em');
select pg_temp.renomear_coluna('moradores', 'created_at', 'criado_em');

select pg_temp.renomear_coluna('abrigos', 'name', 'nome');
select pg_temp.renomear_coluna('abrigos', 'capacity', 'capacidade');
select pg_temp.renomear_coluna('abrigos', 'occupancy', 'ocupacao');
select pg_temp.renomear_coluna('abrigos', 'active', 'ativo');

select pg_temp.renomear_coluna('ocorrencias_manuais', 'status', 'situacao');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'reason', 'motivo');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'operator', 'operador');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'closed_at', 'encerrada_em');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'closed_by', 'encerrada_por');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'created_at', 'criado_em');

-- ---------- Restrições, índices e sequências ----------
-- O PostgreSQL deu nomes a esses objetos a partir dos nomes antigos (ex.: rivers_name_key).
-- Cada nome é traduzido parte por parte, usando a lista abaixo.
create temporary table traducao (antigo text primary key, novo text not null) on commit drop;
insert into traducao values
  ('monitoring_points', 'pontos_monitoramento'), ('point_occurrences', 'ocorrencias'),
  ('measurements', 'medicoes'), ('rivers', 'rios'), ('app_users', 'usuarios'),
  ('audit_events', 'eventos_auditoria'), ('sensor_readings', 'leituras_sensores'),
  ('manual_occurrences', 'ocorrencias_manuais'), ('sensors', 'sensores'), ('residents', 'moradores'),
  ('shelters', 'abrigos'), ('schema_migrations', 'migracoes_aplicadas'),
  ('attention_distance_cm', 'distancia_atencao_cm'), ('alert_distance_cm', 'distancia_alerta_cm'),
  ('critical_distance_cm', 'distancia_critica_cm'), ('min_valid_distance_cm', 'distancia_minima_valida_cm'),
  ('max_valid_distance_cm', 'distancia_maxima_valida_cm'), ('max_jump_cm', 'salto_maximo_cm'),
  ('stale_after_minutes', 'minutos_para_desatualizar'), ('sensor_code', 'codigo_sensor'),
  ('single_active_operator', 'um_operador_ativo'), ('email_unique', 'email_unico'),
  ('point_measured', 'ponto_medida'), ('thresholds_order', 'ordem_limiares'), ('one_open', 'uma_aberta'),
  ('valid_range', 'faixa_valida'), ('river_id', 'rio_id'), ('point_id', 'ponto_id'),
  ('criteria', 'criterios'), ('classification', 'classificacao'), ('origin', 'origem'),
  ('validity', 'validade'), ('unit', 'unidade'), ('role', 'perfil'), ('code', 'codigo'), ('name', 'nome'),
  ('pkey', 'pk'), ('fkey', 'fk'), ('key', 'unico'), ('check', 'regra');

create function pg_temp.traduzir(nome text) returns text language plpgsql as $$
declare
  t record;
  resultado text := '_' || nome || '_';
begin
  for t in select antigo, novo from traducao order by length(antigo) desc loop
    resultado := replace(resultado, '_' || t.antigo || '_', '_' || t.novo || '_');
  end loop;
  return trim(both '_' from resultado);
end $$;

do $$
declare
  r record;
begin
  -- Restrições (chaves primárias, únicas, estrangeiras e regras de verificação).
  for r in select c.conrelid::regclass::text as tabela, c.conname as nome
           from pg_constraint c where c.connamespace = 'public'::regnamespace loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter table public.%I rename constraint %I to %I', r.tabela, r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
  -- Índices que não pertencem a restrições (os de restrições já foram renomeados junto com elas).
  for r in select indexname as nome from pg_indexes where schemaname = 'public' loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter index public.%I rename to %I', r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
  -- Sequências dos ids (ex.: rivers_id_seq).
  for r in select sequencename as nome from pg_sequences where schemaname = 'public' loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter sequence public.%I rename to %I', r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
end $$;

-- ---------- Perfil do operador ----------
alter table public.usuarios drop constraint if exists usuarios_perfil_regra;
drop index if exists public.usuarios_um_operador_ativo_idx;
update public.usuarios set perfil = 'OPERADOR' where perfil = 'OPERATOR';
alter table public.usuarios alter column perfil set default 'OPERADOR';
alter table public.usuarios add constraint usuarios_perfil_regra check (perfil in ('OPERADOR'));
create unique index usuarios_um_operador_ativo_idx on public.usuarios (perfil) where perfil = 'OPERADOR' and ativo is true;

commit;
