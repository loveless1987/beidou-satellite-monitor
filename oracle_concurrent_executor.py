#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle数据库并发SQL执行API服务
提供HTTP接口，支持并发执行多个SQL语句
"""

import oracledb
import concurrent.futures
import time
from typing import List, Tuple, Dict, Any, Optional
from contextlib import contextmanager
import logging
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求


class OracleExecutor:
    def __init__(self, host: str, port: int, service_name: str, username: str, password: str, 
                 max_connections: int = 5):
        """
        初始化Oracle连接执行器
        
        Args:
            host: Oracle服务器地址
            port: 端口号
            service_name: 服务名
            username: 用户名
            password: 密码
            max_connections: 最大连接数
        """
        self.dsn = oracledb.makedsn(host, port, service_name=service_name)
        self.username = username
        self.password = password
        self.max_connections = max_connections
        
        # 初始化连接池
        try:
            self.pool = oracledb.create_pool(
                user=username,
                password=password,
                dsn=self.dsn,
                min=1,
                max=max_connections,
                increment=1
            )
            logger.info(f"成功创建连接池，最大连接数: {max_connections}")
        except Exception as e:
            logger.error(f"创建连接池失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = self.pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"获取连接失败: {e}")
            raise
        finally:
            if connection:
                self.pool.release(connection)

    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None, 
                   fetch_results: bool = True) -> Tuple[bool, Any]:
        """
        执行单个SQL语句
        
        Args:
            sql: SQL语句
            params: 参数字典
            fetch_results: 是否获取查询结果
            
        Returns:
            Tuple[bool, Any]: (执行是否成功, 结果数据或错误信息)
        """
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if fetch_results and sql.strip().upper().startswith('SELECT'):
                    # 查询语句，获取结果
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = {
                        'columns': columns,
                        'rows': rows,
                        'row_count': len(rows)
                    }
                else:
                    # 非查询语句，提交事务
                    conn.commit()
                    result = {
                        'affected_rows': cursor.rowcount,
                        'message': 'SQL执行成功'
                    }
                
                execution_time = time.time() - start_time
                logger.info(f"SQL执行成功，耗时: {execution_time:.2f}秒")
                
                cursor.close()
                return True, result
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"SQL执行失败，耗时: {execution_time:.2f}秒，错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def execute_concurrent(self, sql_list: List[Dict[str, Any]], 
                          max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        并发执行多个SQL语句
        
        Args:
            sql_list: SQL语句列表，每个元素包含:
                - sql: SQL语句
                - params: 参数(可选)
                - name: 任务名称(可选)
                - fetch_results: 是否获取结果(可选，默认True)
            max_workers: 最大并发数
            
        Returns:
            List[Dict]: 执行结果列表
        """
        logger.info(f"开始并发执行 {len(sql_list)} 个SQL语句，最大并发数: {max_workers}")
        
        results = []
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_sql = {}
            for i, sql_info in enumerate(sql_list):
                sql = sql_info['sql']
                params = sql_info.get('params')
                name = sql_info.get('name', f'SQL_{i+1}')
                fetch_results = sql_info.get('fetch_results', True)
                
                future = executor.submit(self.execute_sql, sql, params, fetch_results)
                future_to_sql[future] = {'index': i, 'name': name, 'sql': sql}
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_sql):
                sql_info = future_to_sql[future]
                try:
                    success, result = future.result()
                    results.append({
                        'index': sql_info['index'],
                        'name': sql_info['name'],
                        'sql': sql_info['sql'][:100] + '...' if len(sql_info['sql']) > 100 else sql_info['sql'],
                        'success': success,
                        'result': result
                    })
                    
                    status = "成功" if success else "失败"
                    logger.info(f"任务 '{sql_info['name']}' 执行{status}")
                    
                except Exception as e:
                    results.append({
                        'index': sql_info['index'],
                        'name': sql_info['name'],
                        'sql': sql_info['sql'][:100] + '...' if len(sql_info['sql']) > 100 else sql_info['sql'],
                        'success': False,
                        'result': f"执行异常: {str(e)}"
                    })
                    logger.error(f"任务 '{sql_info['name']}' 执行异常: {e}")
        
        # 按索引排序结果
        results.sort(key=lambda x: x['index'])
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"并发执行完成，总耗时: {total_time:.2f}秒，成功: {success_count}/{len(sql_list)}")
        
        return results

    def close(self):
        """关闭连接池"""
        if hasattr(self, 'pool'):
            self.pool.close()
            logger.info("连接池已关闭")


# 数据库连接配置
DB_CONFIG = {
    'host': '10.211.55.5',        # 修改为你的Oracle服务器地址
    'port': 12223,               # 修改为你的端口
    'service_name': 'swzdh',     # 修改为你的服务名
    'username': 'swzdh', # 修改为你的用户名
    'password': 'dd_1idPLSWwu88_#$i9', # 修改为你的密码
    'max_connections': 5
}

# 全局数据库执行器
executor = None

def init_database():
    """初始化数据库连接"""
    global executor
    try:
        executor = OracleExecutor(**DB_CONFIG)
        logger.info("数据库连接初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'Oracle SQL执行器运行正常',
        'timestamp': time.time()
    })

@app.route('/stations/all', methods=['GET'])
def get_all_stations():
    """获取所有北斗卫星站点状态 - 安全接口（只读）"""
    try:
        if not executor:
            return jsonify({
                'success': False,
                'error': '数据库连接未初始化'
            }), 500
        
        # 预定义的安全SQL查询，SQL硬编码在后端，不接受外部输入
        predefined_sqls = [
            {
                'name': '堡垒雨量站北斗卫星状态',
                'sql': '''select ssb.stcd 测站编码, stnm 测站名称, case when datatype2='245' then '堡垒雨量站' else '加密雨量站' end 站点类型, getCodeName('AD',ADDVCD) 区县, 
                         case when tm is null then '无数据' 
                              when (sysdate - tm > 1) then '离线'||round(sysdate - tm,1)||'天' 
                              else '正常' end 北斗卫星状态, 
                         tm 最后数据时间, case when c is null then 0 else c end 报文数量 
                         from ST_STBPRP_B ssb 
                         left join (select max(tm) tm, stcd from ST_RAIN_RE_BD group by stcd) t1 on t1.stcd = ssb.stcd 
                         left join (select stcd, count(1) c from ST_RAIN_RE_BD where tm > sysdate - 1 group by stcd) t2 on t2.stcd = ssb.stcd 
                         where BD='01' and DATATYPE2 in ('245','JM') order by DATATYPE2''',
                'fetch_results': True
            },
            {
                'name': '水文站北斗卫星状态',
                'sql': '''select ssb.stcd 测站编码, stnm 测站名称, 
                         case when datatype = 'NEW' then '补短板' when datatype = '地埋式水位计' then '地埋式水位计' else '水文站' end 站点类型,  getCodeName('AD',ADDVCD) 区县,
                         case when tm is null then '无数据' 
                              when (sysdate - tm > 1) then '离线'||to_char(round((sysdate - tm),1))||'天' 
                              else '正常' end 北斗卫星状态, 
                         tm 最后数据时间, case when c is null then 0 else c end 报文数量, DATATYPE 
                         from ST_STBPRP_B ssb 
                         left join (select max(tm) tm, stcd from st_river_r_bd group by stcd) t1 on t1.stcd = ssb.stcd 
                         left join (select stcd, count(1) c from st_river_r_bd where tm > sysdate - 1 group by stcd) t2 on t2.stcd = ssb.stcd 
                         where BD='01' and sttp in ('ZZ','ZQ') order by 站点类型''',
                'fetch_results': True
            },
            {
                'name': '墒情站北斗卫星状态',
                'sql': '''select ssb.stcd 测站编码, stnm 测站名称, '墒情站' 站点类型,  getCodeName('AD',ADDVCD) 区县,
                         case when tm is null then '无数据' 
                              when (sysdate - tm > 1) then '离线'||to_char(round((sysdate - tm),1))||'天' 
                              else '正常' end 北斗卫星状态, 
                         tm 最后数据时间, case when c is null then 0 else c end 报文数量 
                         from ST_SQ_B ssb 
                         left join (select max(tm) tm, stcd from ST_MOISTURE_R_BD group by stcd) t1 on t1.stcd = ssb.stcd 
                         left join (select stcd, count(1) c from ST_MOISTURE_R_BD where tm > sysdate - 1 group by stcd) t2 on t2.stcd = ssb.stcd 
                         where BD='01' order by 站点类型''',
                'fetch_results': True
            }
        ]
        
        # 执行预定义的安全查询
        results = executor.execute_concurrent(predefined_sqls, max_workers=3)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'success_count': sum(1 for r in results if r['success']),
                'failed_count': sum(1 for r in results if not r['success'])
            }
        })
        
    except Exception as e:
        logger.error(f"获取站点数据异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

def main():
    """启动API服务"""
    # 初始化数据库连接
    if not init_database():
        logger.error("数据库初始化失败，服务无法启动")
        return
    
    try:
        # 启动Flask服务
        logger.info("启动Oracle SQL执行API服务...")
        app.run(
            host='0.0.0.0',
            port=8071,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
    finally:
        if executor:
            executor.close()

if __name__ == "__main__":
    main()