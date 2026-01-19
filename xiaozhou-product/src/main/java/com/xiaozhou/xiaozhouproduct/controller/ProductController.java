package com.xiaozhou.xiaozhouproduct.controller;

import com.xiaozhou.xiaozhouproduct.entity.Product;
import com.xiaozhou.xiaozhouproduct.feign.OrderFeign;
import com.xiaozhou.xiaozhouproduct.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.logging.Logger;

@RestController
@RequestMapping("/product")
public class ProductController {

    private Logger logger = Logger.getLogger(ProductController.class.getName());

    @Autowired
    private ProductService productService;

    @Autowired
    OrderFeign orderFeign;
    @RequestMapping("/getOrderById")
    private String getOrderById(String id){
        logger.info("nadashd");
        return orderFeign.getOrderById(id);
    }

    // 查询全部商品（分页）
    @GetMapping("page")
    public IPage<Product> getAllProducts(@RequestParam(defaultValue = "1") int pageNum,
                                         @RequestParam(defaultValue = "10") int pageSize) {
        return productService.pageFind(new Page<Product>(pageNum, pageSize));
    }

    // 查询单个商品
    @GetMapping("/{id}")
    public ResponseEntity<Product> getProductById(@PathVariable Integer id) {
        Product product = productService.getById(id);
        return ResponseEntity.ok(product);
    }

    // 新增商品
    @PostMapping("save")
    public ResponseEntity<Product> createProduct(@RequestBody Product product) {
        productService.save(product);
        return ResponseEntity.ok(product);
    }

    // 更新商品
    @PutMapping("/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Integer id, @RequestBody Product product) {
        product.setId(id);
        productService.updateById(product);
        return ResponseEntity.ok(product);
    }

    // 删除商品
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProduct(@PathVariable Integer id) {
        productService.removeById(id);
        return ResponseEntity.ok().build();
    }
}
