package com.xiaozhou.xiaozhoustock.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xiaozhou.xiaozhoustock.entity.Stock;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface StockMapper extends BaseMapper<Stock> {
}
