package com.xiaozhou.xiaozhouproduct.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xiaozhou.xiaozhouproduct.entity.Product;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ProductMapper extends BaseMapper<Product> {
    // MyBatis-Plus已自动实现CRUD方法
}