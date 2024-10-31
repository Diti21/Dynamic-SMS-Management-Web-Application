USE sms_metrics_db; 
CREATE TABLE sms_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country_operator VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sms_sent INT,
    success_rate FLOAT,
    failures INT
);
