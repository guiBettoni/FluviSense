begin;

alter table public.sensors
  drop constraint if exists sensors_thresholds_order_check;

alter table public.sensors
  add constraint sensors_thresholds_order_check check (
    threshold_yellow > 0
    and threshold_yellow < threshold_orange
    and threshold_orange < threshold_red
  );

commit;
