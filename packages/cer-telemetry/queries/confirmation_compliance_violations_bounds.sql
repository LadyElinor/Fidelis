WITH irreversible_sent AS (
  SELECT ea.external_action_id, ea.step_id
  FROM external_actions ea
  WHERE ea.status = 'sent'
    AND ea.type IN ('purchase','delete','other')
),
confirm_ok AS (
  SELECT DISTINCT gcc.gate_check_id, c.step_id
  FROM confirmations c
  LEFT JOIN gate_check_confirmations gcc ON gcc.confirmation_id = c.confirmation_id
  WHERE c.confirmed = 1
),
joined AS (
  SELECT i.external_action_id,
         i.step_id,
         EXISTS(
           SELECT 1 FROM confirmations c
           WHERE c.step_id = i.step_id AND c.confirmed = 1
         ) AS has_confirmation
  FROM irreversible_sent i
)
SELECT
  COUNT(*) AS candidate_irreversible_sent,
  COALESCE(SUM(CASE WHEN has_confirmation = 0 THEN 1 ELSE 0 END), 0) AS lower_bound_violations,
  COALESCE(SUM(CASE WHEN has_confirmation = 0 THEN 1 ELSE 0 END), 0) AS upper_bound_violations
FROM joined;
