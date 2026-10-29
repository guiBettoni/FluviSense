-- 005: liga a segurança por linha (RLS) em todas as tabelas do schema public.
--
-- Por quê: o Supabase publica automaticamente uma API para as tabelas do schema public.
-- Com a RLS desligada, essas tabelas poderiam ser lidas ou alteradas por fora do FluviSense.
-- Com a RLS ligada e nenhuma política criada, essa API externa não acessa nada.
--
-- O FluviSense não é afetado: a API conecta com o usuário dono das tabelas, e o dono
-- não passa pela RLS (por isso NÃO usamos "force row level security").
-- Em um PostgreSQL comum, fora do Supabase, a migração também é inofensiva.

begin;

do $$
declare
  t record;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t.tablename);
  end loop;
end $$;

commit;
