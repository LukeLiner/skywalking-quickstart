package com.xiaozhou.xiaozhoustock.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

@Data
@TableName("stock")
public class Stock implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * Product ID
     */
    private Long productId;

    /**
     * Product name
     */
    private String productName;

    /**
     * Current stock quantity
     */
    private Integer stockQuantity;

    /**
     * Reserved stock quantity
     */
    private Integer reservedStock;

    /**
     * Unit price
     */
    private BigDecimal unitPrice;

    /**
     * Create time
     */
    private Date createTime;

    /**
     * Update time
     */
    private Date updateTime;
}
