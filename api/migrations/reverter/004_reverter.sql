-- Reverte a 004. Apaga SÓ as tabelas criadas por ela (e os dados gravados nelas depois).
-- As tabelas antigas não são tocadas. Faça backup antes de rodar.
-- Se a 006 foi aplicada, rode antes reverter/006_reverter.sql e reverter/005_reverter.sql.
begin;
drop table if exists public.point_occurrences;
drop table if exists public.measurements;
drop table if exists public.monitoring_points;
drop table if exists public.rivers;
delete from public.migracoes_aplicadas where versao = '004_monitoramento_por_distancia';
commit;
