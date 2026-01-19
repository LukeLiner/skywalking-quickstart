package com.xiaozhou.xiaozhouproduct.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.xiaozhou.xiaozhouproduct.entity.Product;

public interface ProductService extends IService<Product> {
    IPage<Product> pageFind(Page<Product> objectPage);
    // 可在此扩展自定义业务方法
}