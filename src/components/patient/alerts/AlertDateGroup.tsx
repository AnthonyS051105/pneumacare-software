import { AlertListItem, type AlertItemData } from "./AlertListItem";

type AlertDateGroupProps = {
  label: string;
  alerts: AlertItemData[];
};

export function AlertDateGroup({ label, alerts }: AlertDateGroupProps) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-on-surface-variant mb-2 px-1">
        {label}
      </h3>
      <div className="flex flex-col gap-3">
        {alerts.map((alert) => (
          <AlertListItem key={alert.id} alert={alert} />
        ))}
      </div>
    </section>
  );
}
