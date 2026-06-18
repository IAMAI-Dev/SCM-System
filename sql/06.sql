-- 补货订单表（无外键约束，兼容所有环境）
CREATE TABLE IF NOT EXISTS scm_replenishment_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    part_key INT NOT NULL,
    supplier_key INT NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);