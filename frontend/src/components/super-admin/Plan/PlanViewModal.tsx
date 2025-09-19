import { Modal, Spin } from "antd";
import { useState, useEffect } from "react";
import type { PlanTableRow } from "../../../TableColumns/useColumnsPlan";
import { getPlanHistory } from "../../../api/post";

interface PlanViewModalProps {
  row: PlanTableRow;
  onClose: () => void;
}

interface PlanHistoryData {
  current_plan: PlanTableRow;
  previous_plans: PlanTableRow[];
  company_name: string;
}

export default function PlanViewModal({ row, onClose }: PlanViewModalProps) {
  const [historyData, setHistoryData] = useState<PlanHistoryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlanHistory = async () => {
      try {
        const response = await getPlanHistory(row.id);
        setHistoryData(response.data);
      } catch (error) {
        console.error("Failed to fetch plan history:", error);
        // Fallback to current row data
        setHistoryData({
          current_plan: row,
          previous_plans: [],
          company_name: row.company_name,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPlanHistory();
  }, [row]);

  return (
    <Modal
      open={true}
      onCancel={onClose}
      footer={null}
      title="Plan Details"
      centered
      width={600}
    >
      {loading ? (
        <div className="flex justify-center items-center p-8">
          <Spin size="large" />
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <strong className="text-lg">Current Plan:</strong>
            <div className="bg-gray-50 p-4 rounded-lg mt-2">
              <div>
                <strong>Plan:</strong>{" "}
                {historyData?.current_plan.plan_name_display || "N/A"}
              </div>
              <div>
                <strong>Plan Price:</strong> ${historyData?.current_plan.price}
              </div>
              <div>
                <strong>Max Agent:</strong>{" "}
                {historyData?.current_plan.max_agents}
              </div>
              <div>
                <strong>Company Name:</strong>{" "}
                {historyData?.current_plan.company_name}
              </div>
              <div>
                <strong>Created Date:</strong>{" "}
                {new Date(
                  historyData?.current_plan.created_at || ""
                ).toLocaleDateString()}
              </div>
              <div>
                <strong>Expiry Date:</strong>{" "}
                {historyData?.current_plan.expiry_date
                  ? new Date(
                      historyData.current_plan.expiry_date
                    ).toLocaleDateString()
                  : "No expiry date set"}
              </div>
            </div>
          </div>

          {historyData?.previous_plans &&
            historyData.previous_plans.length > 0 && (
              <div>
                <strong className="text-lg">Previous Plans:</strong>
                <div className="space-y-2 mt-2">
                  {historyData.previous_plans.map((plan, idx) => (
                    <div key={idx} className="bg-blue-50 p-3 rounded-lg border">
                      <div>
                        <strong>Plan:</strong>{" "}
                        {plan.plan_name_display || plan.plan_name} |{" "}
                        <strong>Price:</strong> ${plan.price} |{" "}
                        <strong>Max Agent:</strong> {plan.max_agents}
                      </div>
                      <div>
                        <strong>Created:</strong>{" "}
                        {new Date(plan.created_at).toLocaleDateString()}
                      </div>
                      <div>
                        <strong>Expiry:</strong>{" "}
                        {plan.expiry_date
                          ? new Date(plan.expiry_date).toLocaleDateString()
                          : "No expiry date set"}
                      </div>
                      {plan.notes && (
                        <div>
                          <strong>Notes:</strong> {plan.notes}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {historyData?.current_plan.notes && (
            <div>
              <strong className="text-lg">Notes:</strong>
              <div className="bg-yellow-50 p-3 rounded-lg mt-2">
                {historyData.current_plan.notes}
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
