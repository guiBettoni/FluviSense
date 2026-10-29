-- Reverte a 005: desliga a RLS. Só use se tiver um motivo claro.
-- Se a 006 foi aplicada, rode antes reverter/006_reverter.sql.
begin;
do $$
declare
  t record;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I disable row level security', t.tablename);
  end loop;
end $$;
delete from public.migracoes_aplicadas where versao = '005_seguranca_por_linha';
commit;
