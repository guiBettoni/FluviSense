-- Reverte a 006: volta os nomes em inglês. Só use se precisar voltar a uma versão antiga do sistema.
-- Rode antes de reverter a 005 e a 004. Faça backup antes.
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

-- Perfil volta a 'OPERATOR'.
alter table public.usuarios drop constraint if exists usuarios_perfil_regra;
drop index if exists public.usuarios_um_operador_ativo_idx;
update public.usuarios set perfil = 'OPERATOR' where perfil = 'OPERADOR';
alter table public.usuarios alter column perfil set default 'OPERATOR';

select pg_temp.renomear_coluna('rios', 'nome', 'name');
select pg_temp.renomear_coluna('rios', 'observacoes', 'notes');
select pg_temp.renomear_coluna('rios', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('pontos_monitoramento', 'codigo', 'code');
select pg_temp.renomear_coluna('pontos_monitoramento', 'nome', 'name');
select pg_temp.renomear_coluna('pontos_monitoramento', 'rio_id', 'river_id');
select pg_temp.renomear_coluna('pontos_monitoramento', 'bairro', 'neighborhood');
select pg_temp.renomear_coluna('pontos_monitoramento', 'descricao_local', 'location_description');
select pg_temp.renomear_coluna('pontos_monitoramento', 'distancia_atencao_cm', 'attention_distance_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'distancia_alerta_cm', 'alert_distance_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'distancia_critica_cm', 'critical_distance_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'criterios_provisorios', 'criteria_provisional');
select pg_temp.renomear_coluna('pontos_monitoramento', 'justificativa_criterios', 'criteria_note');
select pg_temp.renomear_coluna('pontos_monitoramento', 'distancia_minima_valida_cm', 'min_valid_distance_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'distancia_maxima_valida_cm', 'max_valid_distance_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'salto_maximo_cm', 'max_jump_cm');
select pg_temp.renomear_coluna('pontos_monitoramento', 'minutos_para_desatualizar', 'stale_after_minutes');
select pg_temp.renomear_coluna('pontos_monitoramento', 'hash_chave_sensor', 'device_key_hash');
select pg_temp.renomear_coluna('pontos_monitoramento', 'ativo', 'active');
select pg_temp.renomear_coluna('pontos_monitoramento', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('pontos_monitoramento', 'atualizado_em', 'updated_at');
select pg_temp.renomear_coluna('medicoes', 'ponto_id', 'point_id');
select pg_temp.renomear_coluna('medicoes', 'distancia_cm', 'distance_cm');
select pg_temp.renomear_coluna('medicoes', 'unidade', 'unit');
select pg_temp.renomear_coluna('medicoes', 'origem', 'origin');
select pg_temp.renomear_coluna('medicoes', 'medida_em', 'measured_at');
select pg_temp.renomear_coluna('medicoes', 'recebida_em', 'received_at');
select pg_temp.renomear_coluna('medicoes', 'validade', 'validity');
select pg_temp.renomear_coluna('medicoes', 'motivo_validade', 'validity_reason');
select pg_temp.renomear_coluna('medicoes', 'referencia_cm', 'reference_cm');
select pg_temp.renomear_coluna('medicoes', 'classificacao', 'classification');
select pg_temp.renomear_coluna('medicoes', 'registrada_por', 'created_by');
select pg_temp.renomear_coluna('ocorrencias', 'ponto_id', 'point_id');
select pg_temp.renomear_coluna('ocorrencias', 'classificacao', 'classification');
select pg_temp.renomear_coluna('ocorrencias', 'motivo', 'reason');
select pg_temp.renomear_coluna('ocorrencias', 'aberta_por', 'opened_by');
select pg_temp.renomear_coluna('ocorrencias', 'aberta_em', 'opened_at');
select pg_temp.renomear_coluna('ocorrencias', 'encerrada_em', 'closed_at');
select pg_temp.renomear_coluna('ocorrencias', 'encerrada_por', 'closed_by');
select pg_temp.renomear_coluna('usuarios', 'nome', 'name');
select pg_temp.renomear_coluna('usuarios', 'hash_senha', 'password_hash');
select pg_temp.renomear_coluna('usuarios', 'perfil', 'role');
select pg_temp.renomear_coluna('usuarios', 'ativo', 'active');
select pg_temp.renomear_coluna('usuarios', 'ultimo_login_em', 'last_login_at');
select pg_temp.renomear_coluna('usuarios', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('eventos_auditoria', 'autor', 'actor');
select pg_temp.renomear_coluna('eventos_auditoria', 'acao', 'action');
select pg_temp.renomear_coluna('eventos_auditoria', 'entidade', 'entity');
select pg_temp.renomear_coluna('eventos_auditoria', 'detalhes', 'details');
select pg_temp.renomear_coluna('eventos_auditoria', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('sensores', 'codigo_sensor', 'sensor_code');
select pg_temp.renomear_coluna('sensores', 'nome', 'name');
select pg_temp.renomear_coluna('sensores', 'bairro', 'neighborhood');
select pg_temp.renomear_coluna('sensores', 'descricao_local', 'location_description');
select pg_temp.renomear_coluna('sensores', 'limiar_amarelo', 'threshold_yellow');
select pg_temp.renomear_coluna('sensores', 'limiar_laranja', 'threshold_orange');
select pg_temp.renomear_coluna('sensores', 'limiar_vermelho', 'threshold_red');
select pg_temp.renomear_coluna('sensores', 'nivel_atual', 'current_level');
select pg_temp.renomear_coluna('sensores', 'situacao_atual', 'current_status');
select pg_temp.renomear_coluna('sensores', 'ativo', 'active');
select pg_temp.renomear_coluna('sensores', 'ultima_leitura_em', 'last_reading_at');
select pg_temp.renomear_coluna('sensores', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('leituras_sensores', 'nivel_agua_cm', 'water_level_cm');
select pg_temp.renomear_coluna('leituras_sensores', 'origem', 'origin');
select pg_temp.renomear_coluna('leituras_sensores', 'situacao_gerada', 'status_generated');
select pg_temp.renomear_coluna('leituras_sensores', 'valida', 'is_valid');
select pg_temp.renomear_coluna('leituras_sensores', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('moradores', 'nome', 'name');
select pg_temp.renomear_coluna('moradores', 'bairro', 'neighborhood');
select pg_temp.renomear_coluna('moradores', 'rua', 'street');
select pg_temp.renomear_coluna('moradores', 'consentimento_em', 'consent_at');
select pg_temp.renomear_coluna('moradores', 'criado_em', 'created_at');
select pg_temp.renomear_coluna('abrigos', 'nome', 'name');
select pg_temp.renomear_coluna('abrigos', 'capacidade', 'capacity');
select pg_temp.renomear_coluna('abrigos', 'ocupacao', 'occupancy');
select pg_temp.renomear_coluna('abrigos', 'ativo', 'active');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'situacao', 'status');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'motivo', 'reason');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'operador', 'operator');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'encerrada_em', 'closed_at');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'encerrada_por', 'closed_by');
select pg_temp.renomear_coluna('ocorrencias_manuais', 'criado_em', 'created_at');

select pg_temp.renomear_tabela('rios', 'rivers');
select pg_temp.renomear_tabela('pontos_monitoramento', 'monitoring_points');
select pg_temp.renomear_tabela('medicoes', 'measurements');
select pg_temp.renomear_tabela('ocorrencias', 'point_occurrences');
select pg_temp.renomear_tabela('usuarios', 'app_users');
select pg_temp.renomear_tabela('eventos_auditoria', 'audit_events');
select pg_temp.renomear_tabela('sensores', 'sensors');
select pg_temp.renomear_tabela('leituras_sensores', 'sensor_readings');
select pg_temp.renomear_tabela('moradores', 'residents');
select pg_temp.renomear_tabela('abrigos', 'shelters');
select pg_temp.renomear_tabela('ocorrencias_manuais', 'manual_occurrences');

-- Restrições, índices e sequências: tradução inversa, parte por parte.
create temporary table traducao (antigo text primary key, novo text not null) on commit drop;
insert into traducao values
  ('pontos_monitoramento', 'monitoring_points'),
  ('ocorrencias', 'point_occurrences'),
  ('medicoes', 'measurements'),
  ('rios', 'rivers'),
  ('usuarios', 'app_users'),
  ('eventos_auditoria', 'audit_events'),
  ('leituras_sensores', 'sensor_readings'),
  ('ocorrencias_manuais', 'manual_occurrences'),
  ('sensores', 'sensors'),
  ('moradores', 'residents'),
  ('abrigos', 'shelters'),
  ('distancia_atencao_cm', 'attention_distance_cm'),
  ('distancia_alerta_cm', 'alert_distance_cm'),
  ('distancia_critica_cm', 'critical_distance_cm'),
  ('distancia_minima_valida_cm', 'min_valid_distance_cm'),
  ('distancia_maxima_valida_cm', 'max_valid_distance_cm'),
  ('salto_maximo_cm', 'max_jump_cm'),
  ('minutos_para_desatualizar', 'stale_after_minutes'),
  ('codigo_sensor', 'sensor_code'),
  ('um_operador_ativo', 'single_active_operator'),
  ('email_unico', 'email_unique'),
  ('ponto_medida', 'point_measured'),
  ('ordem_limiares', 'thresholds_order'),
  ('uma_aberta', 'one_open'),
  ('faixa_valida', 'valid_range'),
  ('rio_id', 'river_id'),
  ('ponto_id', 'point_id'),
  ('criterios', 'criteria'),
  ('classificacao', 'classification'),
  ('origem', 'origin'),
  ('validade', 'validity'),
  ('unidade', 'unit'),
  ('perfil', 'role'),
  ('codigo', 'code'),
  ('nome', 'name'),
  ('pk', 'pkey'),
  ('fk', 'fkey'),
  ('unico', 'key'),
  ('regra', 'check');

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
  for r in select c.conrelid::regclass::text as tabela, c.conname as nome
           from pg_constraint c where c.connamespace = 'public'::regnamespace
             and c.conrelid::regclass::text <> 'migracoes_aplicadas' loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter table public.%I rename constraint %I to %I', r.tabela, r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
  for r in select indexname as nome from pg_indexes where schemaname = 'public' and tablename <> 'migracoes_aplicadas' loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter index public.%I rename to %I', r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
  for r in select sequencename as nome from pg_sequences where schemaname = 'public' loop
    if pg_temp.traduzir(r.nome) <> r.nome then
      execute format('alter sequence public.%I rename to %I', r.nome, pg_temp.traduzir(r.nome));
    end if;
  end loop;
end $$;

alter table public.app_users add constraint app_users_role_check check (role in ('OPERATOR'));
create unique index app_users_single_active_operator_idx on public.app_users (role) where role = 'OPERATOR' and active is true;

delete from public.migracoes_aplicadas where versao = '006_nomes_em_portugues';
commit;
