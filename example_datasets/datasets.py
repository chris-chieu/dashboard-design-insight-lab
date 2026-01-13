"""
Dataset Configurations
Centralized repository for dataset definitions used in dashboard generation
"""

# Available datasets for dashboard creation
DATASETS = {
    "nyc_taxi": {
        "name": "nyc_taxi_001",
        "displayName": "NYC Taxi",
        "queryLines": [
            "SELECT\n",
            "  T.tpep_pickup_datetime,\n",
            "  T.tpep_dropoff_datetime,\n",
            "  T.fare_amount,\n",
            "  T.pickup_zip,\n",
            "  T.dropoff_zip,\n",
            "  T.trip_distance,\n",
            "  T.weekday,\n",
            "  CASE\n",
            "    WHEN T.weekday = 1 THEN 'Sunday'\n",
            "    WHEN T.weekday = 2 THEN 'Monday'\n",
            "    WHEN T.weekday = 3 THEN 'Tuesday'\n",
            "    WHEN T.weekday = 4 THEN 'Wednesday'\n",
            "    WHEN T.weekday = 5 THEN 'Thursday'\n",
            "    WHEN T.weekday = 6 THEN 'Friday'\n",
            "    WHEN T.weekday = 7 THEN 'Saturday'\n",
            "    ELSE 'N/A'\n",
            "  END AS day_of_week\n",
            "FROM\n",
            "  (\n",
            "    SELECT\n",
            "      dayofweek(tpep_pickup_datetime) as weekday,\n",
            "      *\n",
            "    FROM\n",
            "      `users`.`nilay_tiwari`.taxi_trips\n",
            "    WHERE\n",
            "      trip_distance > 0\n",
            "      AND trip_distance < 10\n",
            "      AND fare_amount > 0\n",
            "      AND fare_amount < 50\n",
            "  ) T\n",
            "ORDER BY\n",
            "  T.weekday"
        ]
    },
    "support": {
        "name": "39a5402c",
        "displayName": "Support Data",
        "queryLines": [
            "WITH TopTopics AS (\n",
            "  SELECT\n",
            "    topic\n",
            "  FROM\n",
            "    christophe_chieu.customer_support.tickets_clean\n",
            "  GROUP BY\n",
            "    topic\n",
            "  ORDER BY\n",
            "    COUNT(ticket_id) DESC\n",
            "  LIMIT 5\n",
            "),\n",
            "TopCountries AS (\n",
            "  SELECT\n",
            "    country\n",
            "  FROM\n",
            "    christophe_chieu.customer_support.tickets_clean\n",
            "  GROUP BY\n",
            "    country\n",
            "  ORDER BY\n",
            "    COUNT(ticket_id) DESC\n",
            "  LIMIT 4\n",
            ")\n",
            "SELECT\n",
            "  t.ticket_id,\n",
            "  s.expected_sla_to_resolve,\n",
            "  s.expected_sla_to_first_response,\n",
            "  s.first_response_time,\n",
            "  s.sla_for_first_response,\n",
            "  s.resolution_time,\n",
            "  s.sla_for_resolution,\n",
            "  s.survey_results,\n",
            "  a.agent_group,\n",
            "  a.agent_name,\n",
            "  a.agent_interactions,\n",
            "  t.status,\n",
            "  t.priority,\n",
            "  t.source,\n",
            "  t.topic,\n",
            "  t.created_time,\n",
            "  t.close_time,\n",
            "  t.product_group,\n",
            "  t.support_level,\n",
            "  t.country,\n",
            "  t.latitude,\n",
            "  t.longitude,\n",
            "  (\n",
            "    TIMESTAMPDIFF(MINUTE, t.created_time, s.resolution_time)\n",
            "    + CASE\n",
            "      WHEN t.support_level = 'Tier 2' THEN FLOOR(3000 + (RAND() * (3000 - 2400)))\n",
            "      ELSE 0\n",
            "    END\n",
            "  )\n",
            "  / 60.0 AS adjusted_resolution_time\n",
            "FROM\n",
            "  christophe_chieu.customer_support.sla_clean s\n",
            "    JOIN christophe_chieu.customer_support.agents_clean a USING (ticket_id)\n",
            "    JOIN christophe_chieu.customer_support.tickets_clean t USING (ticket_id)\n",
            "WHERE\n",
            "  t.topic IN (\n",
            "    SELECT\n",
            "      topic\n",
            "    FROM\n",
            "      TopTopics\n",
            "  )\n",
            "  AND t.country IN (\n",
            "    SELECT\n",
            "      country\n",
            "    FROM\n",
            "      TopCountries\n",
            "  )\n",
            "  AND TIMESTAMPDIFF(MINUTE, t.created_time, s.resolution_time) != 0;"
        ]
    }
}


def get_dataset(dataset_key: str) -> dict:
    """
    Get dataset configuration by key
    
    Args:
        dataset_key: Dataset identifier key
        
    Returns:
        Dataset configuration dictionary or None if not found
    """
    return DATASETS.get(dataset_key)


def get_all_datasets() -> dict:
    """
    Get all available datasets
    
    Returns:
        Dictionary of all dataset configurations
    """
    return DATASETS

