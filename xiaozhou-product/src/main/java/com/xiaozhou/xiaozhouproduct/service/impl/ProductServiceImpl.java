package com.xiaozhou.xiaozhouproduct.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xiaozhou.xiaozhouproduct.entity.Product;
import com.xiaozhou.xiaozhouproduct.mapper.ProductMapper;
import com.xiaozhou.xiaozhouproduct.service.ProductService;
import org.apache.skywalking.apm.toolkit.trace.Tag;
import org.apache.skywalking.apm.toolkit.trace.Trace;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ProductServiceImpl extends ServiceImpl<ProductMapper, Product> implements ProductService {
    @Autowired
    private ProductMapper productMapper;
    @Override
    @Trace
    @Tag(key = "pageFind", value = "returnedObj")
    public IPage<Product> pageFind(Page<Product> objectPage) {
        return productMapper.selectPage(objectPage, null);
    }
    // 可在此覆盖默认方法或添加自定义逻辑
}