"""
Client Agent - 거래처 분석 Agent

고객 데이터 분석, 거래 이력, 매출 분석, 비즈니스 인사이트를 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional
import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from ...core.config import settings
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class ClientAgent:
    """거래처 분석 Agent"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        
        # 고객 데이터베이스 경로
        self.client_db_path = Path(settings.sqlite_db_path) / "client_data.db"
        
        # 분석 타입 정의
        self.analysis_types = {
            "profile": "고객 프로필 분석",
            "transaction": "거래 이력 분석", 
            "sales": "매출 분석",
            "trend": "트렌드 분석",
            "risk": "위험도 분석",
            "opportunity": "기회 분석"
        }
        
        # 분석 지표 정의
        self.available_metrics = [
            "매출액", "거래횟수", "평균주문금액", "고객만족도", 
            "리텐션율", "신규고객비율", "마진율", "성장률"
        ]
        
        logger.info("Client Agent 초기화 완료")
    
    async def process(self, args: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Client Agent 메인 처리 함수"""
        try:
            analysis_type = args.get("analysis_type")
            client_id = args.get("client_id")
            time_period = args.get("time_period", "2024-01~2024-12")
            metrics = args.get("metrics", ["매출액", "거래횟수"])
            
            logger.info(f"Client Agent 처리: {analysis_type} 분석 - {client_id or 'ALL'}")
            
            # 분석 타입에 따른 처리
            if analysis_type == "profile":
                results = await self._analyze_client_profile(client_id, time_period)
            elif analysis_type == "transaction":
                results = await self._analyze_transactions(client_id, time_period, metrics)
            elif analysis_type == "sales":
                results = await self._analyze_sales(client_id, time_period, metrics)
            elif analysis_type == "trend":
                results = await self._analyze_trends(client_id, time_period, metrics)
            elif analysis_type == "risk":
                results = await self._analyze_risks(client_id, time_period)
            elif analysis_type == "opportunity":
                results = await self._analyze_opportunities(client_id, time_period)
            else:
                # 종합 분석
                results = await self._comprehensive_analysis(client_id, time_period, metrics)
            
            if results["data"]:
                response = await self._format_analysis_response(results, analysis_type, client_id)
                
                return {
                    "response": response,
                    "sources": results["sources"],
                    "metadata": {
                        "agent": "client_agent",
                        "analysis_type": analysis_type,
                        "client_id": client_id,
                        "time_period": time_period,
                        "metrics": metrics,
                        "data_points": len(results["data"])
                    }
                }
            else:
                return {
                    "response": f"'{client_id or '전체 고객'}'에 대한 {self.analysis_types.get(analysis_type, '분석')} 데이터를 찾을 수 없습니다.",
                    "sources": [],
                    "metadata": {
                        "agent": "client_agent",
                        "analysis_type": analysis_type,
                        "data_points": 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Client Agent 처리 실패: {str(e)}")
            return {
                "response": f"고객 분석 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e), "agent": "client_agent"}
            }
    
    async def _analyze_client_profile(self, client_id: Optional[str], time_period: str) -> Dict[str, Any]:
        """고객 프로필 분석"""
        try:
            if client_id:
                # 특정 고객 프로필
                profile_data = await self._get_client_profile(client_id)
            else:
                # 전체 고객 프로필 요약
                profile_data = await self._get_all_clients_summary()
            
            return {
                "data": profile_data,
                "sources": [{"type": "client_database", "analysis": "profile", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"고객 프로필 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _analyze_transactions(self, client_id: Optional[str], time_period: str, metrics: List[str]) -> Dict[str, Any]:
        """거래 이력 분석"""
        try:
            transaction_data = await self._get_transaction_data(client_id, time_period)
            
            # 지표별 분석
            analysis_results = {}
            for metric in metrics:
                if metric == "거래횟수":
                    analysis_results[metric] = len(transaction_data)
                elif metric == "매출액":
                    analysis_results[metric] = sum(t.get("amount", 0) for t in transaction_data)
                elif metric == "평균주문금액":
                    if transaction_data:
                        analysis_results[metric] = sum(t.get("amount", 0) for t in transaction_data) / len(transaction_data)
                    else:
                        analysis_results[metric] = 0
            
            return {
                "data": {
                    "transactions": transaction_data,
                    "metrics": analysis_results,
                    "summary": self._create_transaction_summary(transaction_data)
                },
                "sources": [{"type": "transaction_database", "analysis": "transactions", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"거래 이력 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _analyze_sales(self, client_id: Optional[str], time_period: str, metrics: List[str]) -> Dict[str, Any]:
        """매출 분석"""
        try:
            sales_data = await self._get_sales_data(client_id, time_period)
            
            # 매출 지표 계산
            total_sales = sum(s.get("amount", 0) for s in sales_data)
            avg_sales = total_sales / len(sales_data) if sales_data else 0
            
            # 월별 매출 분석
            monthly_sales = self._group_sales_by_month(sales_data)
            
            # 성장률 계산
            growth_rate = self._calculate_growth_rate(monthly_sales)
            
            return {
                "data": {
                    "total_sales": total_sales,
                    "average_sales": avg_sales,
                    "monthly_sales": monthly_sales,
                    "growth_rate": growth_rate,
                    "transaction_count": len(sales_data)
                },
                "sources": [{"type": "sales_database", "analysis": "sales", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"매출 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _analyze_trends(self, client_id: Optional[str], time_period: str, metrics: List[str]) -> Dict[str, Any]:
        """트렌드 분석"""
        try:
            trend_data = await self._get_trend_data(client_id, time_period)
            
            # 트렌드 패턴 분석
            trends = {
                "increasing": [],
                "decreasing": [],
                "stable": []
            }
            
            for metric in metrics:
                trend_direction = self._analyze_metric_trend(trend_data, metric)
                trends[trend_direction].append(metric)
            
            return {
                "data": {
                    "trends": trends,
                    "trend_data": trend_data,
                    "forecast": self._generate_forecast(trend_data)
                },
                "sources": [{"type": "trend_analysis", "analysis": "trends", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"트렌드 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _analyze_risks(self, client_id: Optional[str], time_period: str) -> Dict[str, Any]:
        """위험도 분석"""
        try:
            risk_data = await self._assess_client_risks(client_id, time_period)
            
            # 위험 요소 평가
            risk_factors = {
                "payment_delay": self._check_payment_delays(risk_data),
                "transaction_decline": self._check_transaction_decline(risk_data),
                "credit_risk": self._assess_credit_risk(risk_data),
                "concentration_risk": self._assess_concentration_risk(risk_data)
            }
            
            # 종합 위험도 산출
            overall_risk = self._calculate_overall_risk(risk_factors)
            
            return {
                "data": {
                    "risk_factors": risk_factors,
                    "overall_risk": overall_risk,
                    "recommendations": self._generate_risk_recommendations(risk_factors)
                },
                "sources": [{"type": "risk_assessment", "analysis": "risks", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"위험도 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _analyze_opportunities(self, client_id: Optional[str], time_period: str) -> Dict[str, Any]:
        """기회 분석"""
        try:
            opportunity_data = await self._identify_opportunities(client_id, time_period)
            
            # 기회 유형별 분석
            opportunities = {
                "upselling": self._identify_upselling_opportunities(opportunity_data),
                "cross_selling": self._identify_cross_selling_opportunities(opportunity_data),
                "expansion": self._identify_expansion_opportunities(opportunity_data),
                "retention": self._identify_retention_opportunities(opportunity_data)
            }
            
            # 우선순위 평가
            prioritized_opportunities = self._prioritize_opportunities(opportunities)
            
            return {
                "data": {
                    "opportunities": opportunities,
                    "prioritized": prioritized_opportunities,
                    "action_items": self._generate_action_items(prioritized_opportunities)
                },
                "sources": [{"type": "opportunity_analysis", "analysis": "opportunities", "client_id": client_id}]
            }
            
        except Exception as e:
            logger.error(f"기회 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _comprehensive_analysis(self, client_id: Optional[str], time_period: str, metrics: List[str]) -> Dict[str, Any]:
        """종합 분석"""
        try:
            # 각 분석 타입의 결과를 종합
            profile_result = await self._analyze_client_profile(client_id, time_period)
            sales_result = await self._analyze_sales(client_id, time_period, metrics)
            risk_result = await self._analyze_risks(client_id, time_period)
            opportunity_result = await self._analyze_opportunities(client_id, time_period)
            
            # 종합 인사이트 생성
            comprehensive_insights = self._generate_comprehensive_insights({
                "profile": profile_result["data"],
                "sales": sales_result["data"],
                "risks": risk_result["data"],
                "opportunities": opportunity_result["data"]
            })
            
            return {
                "data": {
                    "profile": profile_result["data"],
                    "sales": sales_result["data"],
                    "risks": risk_result["data"],
                    "opportunities": opportunity_result["data"],
                    "insights": comprehensive_insights
                },
                "sources": [
                    {"type": "comprehensive_analysis", "analysis": "all", "client_id": client_id}
                ] + profile_result["sources"] + sales_result["sources"] + risk_result["sources"] + opportunity_result["sources"]
            }
            
        except Exception as e:
            logger.error(f"종합 분석 실패: {str(e)}")
            return {"data": [], "sources": []}
    
    async def _get_client_profile(self, client_id: str) -> Dict[str, Any]:
        """특정 고객 프로필 조회"""
        # 샘플 데이터 (실제로는 데이터베이스에서 조회)
        return {
            "client_id": client_id,
            "name": f"고객_{client_id}",
            "type": "법인",
            "industry": "제조업",
            "registration_date": "2023-01-15",
            "last_transaction": "2024-07-10",
            "status": "활성"
        }
    
    async def _get_all_clients_summary(self) -> Dict[str, Any]:
        """전체 고객 요약"""
        return {
            "total_clients": 150,
            "active_clients": 120,
            "new_clients_this_month": 8,
            "top_industries": ["제조업", "서비스업", "IT"],
            "client_distribution": {
                "대기업": 30,
                "중소기업": 90,
                "개인사업자": 30
            }
        }
    
    async def _get_transaction_data(self, client_id: Optional[str], time_period: str) -> List[Dict[str, Any]]:
        """거래 데이터 조회"""
        # 샘플 데이터
        return [
            {"date": "2024-07-01", "amount": 1500000, "product": "제품A", "quantity": 10},
            {"date": "2024-07-05", "amount": 2300000, "product": "제품B", "quantity": 15},
            {"date": "2024-07-10", "amount": 1800000, "product": "제품A", "quantity": 12}
        ]
    
    async def _get_sales_data(self, client_id: Optional[str], time_period: str) -> List[Dict[str, Any]]:
        """매출 데이터 조회"""
        return await self._get_transaction_data(client_id, time_period)
    
    async def _get_trend_data(self, client_id: Optional[str], time_period: str) -> Dict[str, List]:
        """트렌드 데이터 조회"""
        return {
            "매출액": [1500000, 2300000, 1800000, 2100000, 2500000],
            "거래횟수": [3, 5, 4, 6, 7],
            "월별": ["2024-03", "2024-04", "2024-05", "2024-06", "2024-07"]
        }
    
    async def _assess_client_risks(self, client_id: Optional[str], time_period: str) -> Dict[str, Any]:
        """고객 위험도 평가 데이터"""
        return {
            "payment_history": {"delays": 2, "total_payments": 20},
            "transaction_volume": {"current_month": 5, "previous_month": 7},
            "credit_score": 75,
            "industry_risk": "중간"
        }
    
    async def _identify_opportunities(self, client_id: Optional[str], time_period: str) -> Dict[str, Any]:
        """기회 식별 데이터"""
        return {
            "purchase_patterns": ["제품A 선호", "월말 주문 집중"],
            "unused_products": ["제품C", "제품D"],
            "competitor_analysis": {"weak_areas": ["가격", "납기"]},
            "seasonal_trends": {"peak_months": ["11월", "12월"]}
        }
    
    # 분석 헬퍼 메서드들
    def _create_transaction_summary(self, transactions: List[Dict]) -> Dict[str, Any]:
        """거래 요약 생성"""
        if not transactions:
            return {"error": "거래 데이터가 없습니다."}
        
        return {
            "total_transactions": len(transactions),
            "total_amount": sum(t.get("amount", 0) for t in transactions),
            "average_amount": sum(t.get("amount", 0) for t in transactions) / len(transactions),
            "date_range": {
                "start": min(t.get("date", "") for t in transactions),
                "end": max(t.get("date", "") for t in transactions)
            }
        }
    
    def _group_sales_by_month(self, sales_data: List[Dict]) -> Dict[str, float]:
        """월별 매출 그룹화"""
        monthly = {}
        for sale in sales_data:
            month = sale.get("date", "")[:7]  # YYYY-MM 형식
            monthly[month] = monthly.get(month, 0) + sale.get("amount", 0)
        return monthly
    
    def _calculate_growth_rate(self, monthly_sales: Dict[str, float]) -> float:
        """성장률 계산"""
        if len(monthly_sales) < 2:
            return 0.0
        
        months = sorted(monthly_sales.keys())
        if len(months) >= 2:
            current = monthly_sales[months[-1]]
            previous = monthly_sales[months[-2]]
            return ((current - previous) / previous * 100) if previous > 0 else 0.0
        return 0.0
    
    def _analyze_metric_trend(self, trend_data: Dict, metric: str) -> str:
        """지표 트렌드 방향 분석"""
        if metric not in trend_data:
            return "stable"
        
        values = trend_data[metric]
        if len(values) < 3:
            return "stable"
        
        # 간단한 트렌드 분석
        recent_avg = sum(values[-3:]) / 3
        earlier_avg = sum(values[:3]) / 3
        
        if recent_avg > earlier_avg * 1.1:
            return "increasing"
        elif recent_avg < earlier_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_forecast(self, trend_data: Dict) -> Dict[str, Any]:
        """예측 생성"""
        return {
            "next_month_sales": 2800000,
            "confidence": 75,
            "factors": ["계절성", "과거 패턴", "시장 트렌드"]
        }
    
    # 위험도 분석 헬퍼 메서드들
    def _check_payment_delays(self, risk_data: Dict) -> Dict[str, Any]:
        """결제 지연 확인"""
        payment_info = risk_data.get("payment_history", {})
        delays = payment_info.get("delays", 0)
        total = payment_info.get("total_payments", 1)
        
        delay_rate = delays / total
        risk_level = "높음" if delay_rate > 0.2 else "중간" if delay_rate > 0.1 else "낮음"
        
        return {"delay_rate": delay_rate, "risk_level": risk_level}
    
    def _check_transaction_decline(self, risk_data: Dict) -> Dict[str, Any]:
        """거래 감소 확인"""
        volume = risk_data.get("transaction_volume", {})
        current = volume.get("current_month", 0)
        previous = volume.get("previous_month", 1)
        
        decline_rate = (previous - current) / previous if previous > 0 else 0
        risk_level = "높음" if decline_rate > 0.3 else "중간" if decline_rate > 0.1 else "낮음"
        
        return {"decline_rate": decline_rate, "risk_level": risk_level}
    
    def _assess_credit_risk(self, risk_data: Dict) -> Dict[str, Any]:
        """신용 위험도 평가"""
        credit_score = risk_data.get("credit_score", 50)
        risk_level = "낮음" if credit_score > 80 else "중간" if credit_score > 60 else "높음"
        
        return {"credit_score": credit_score, "risk_level": risk_level}
    
    def _assess_concentration_risk(self, risk_data: Dict) -> Dict[str, Any]:
        """집중도 위험 평가"""
        # 업계 위험도 등을 고려한 집중도 위험
        industry_risk = risk_data.get("industry_risk", "중간")
        return {"industry_risk": industry_risk, "risk_level": industry_risk}
    
    def _calculate_overall_risk(self, risk_factors: Dict) -> Dict[str, Any]:
        """종합 위험도 계산"""
        risk_scores = {
            "높음": 3,
            "중간": 2,
            "낮음": 1
        }
        
        total_score = 0
        factor_count = 0
        
        for factor, data in risk_factors.items():
            if isinstance(data, dict) and "risk_level" in data:
                total_score += risk_scores.get(data["risk_level"], 2)
                factor_count += 1
        
        avg_score = total_score / factor_count if factor_count > 0 else 2
        
        if avg_score >= 2.5:
            overall_level = "높음"
        elif avg_score >= 1.5:
            overall_level = "중간"
        else:
            overall_level = "낮음"
        
        return {"score": avg_score, "level": overall_level}
    
    def _generate_risk_recommendations(self, risk_factors: Dict) -> List[str]:
        """위험도 기반 권고사항 생성"""
        recommendations = []
        
        for factor, data in risk_factors.items():
            if isinstance(data, dict) and data.get("risk_level") == "높음":
                if factor == "payment_delay":
                    recommendations.append("결제 조건 재검토 및 신용 한도 조정 필요")
                elif factor == "transaction_decline":
                    recommendations.append("고객 관계 강화 및 니즈 파악 필요")
                elif factor == "credit_risk":
                    recommendations.append("신용 조사 업데이트 및 보증 요구 검토")
        
        if not recommendations:
            recommendations.append("현재 위험 수준이 낮아 정기 모니터링만 필요")
        
        return recommendations
    
    # 기회 분석 헬퍼 메서드들
    def _identify_upselling_opportunities(self, opportunity_data: Dict) -> List[Dict]:
        """업셀링 기회 식별"""
        return [
            {"product": "제품A 프리미엄", "potential_revenue": 500000, "probability": 0.7}
        ]
    
    def _identify_cross_selling_opportunities(self, opportunity_data: Dict) -> List[Dict]:
        """크로스셀링 기회 식별"""
        unused = opportunity_data.get("unused_products", [])
        return [
            {"product": product, "potential_revenue": 300000, "probability": 0.5}
            for product in unused
        ]
    
    def _identify_expansion_opportunities(self, opportunity_data: Dict) -> List[Dict]:
        """확장 기회 식별"""
        return [
            {"opportunity": "신규 사업부 진출", "potential_revenue": 2000000, "probability": 0.4}
        ]
    
    def _identify_retention_opportunities(self, opportunity_data: Dict) -> List[Dict]:
        """고객 유지 기회 식별"""
        return [
            {"action": "로열티 프로그램 제안", "retention_impact": 0.8, "cost": 100000}
        ]
    
    def _prioritize_opportunities(self, opportunities: Dict) -> List[Dict]:
        """기회 우선순위 평가"""
        all_opportunities = []
        
        for category, items in opportunities.items():
            for item in items:
                priority_score = item.get("potential_revenue", 0) * item.get("probability", 0)
                all_opportunities.append({
                    "category": category,
                    "item": item,
                    "priority_score": priority_score
                })
        
        return sorted(all_opportunities, key=lambda x: x["priority_score"], reverse=True)[:5]
    
    def _generate_action_items(self, prioritized_opportunities: List[Dict]) -> List[str]:
        """실행 과제 생성"""
        action_items = []
        
        for i, opp in enumerate(prioritized_opportunities[:3], 1):
            category = opp["category"]
            if category == "upselling":
                action_items.append(f"{i}. 프리미엄 제품 제안서 작성 및 고객 미팅 일정 수립")
            elif category == "cross_selling":
                action_items.append(f"{i}. 미사용 제품 데모 및 체험 기회 제공")
            elif category == "expansion":
                action_items.append(f"{i}. 신규 비즈니스 영역 제안서 준비")
            elif category == "retention":
                action_items.append(f"{i}. 고객 만족도 조사 및 개선방안 수립")
        
        return action_items
    
    def _generate_comprehensive_insights(self, all_data: Dict) -> List[str]:
        """종합 인사이트 생성"""
        insights = []
        
        # 매출 기반 인사이트
        sales_data = all_data.get("sales", {})
        if sales_data.get("growth_rate", 0) > 10:
            insights.append("🔥 매출 성장률이 높아 확장 투자를 고려할 시점입니다.")
        
        # 위험도 기반 인사이트
        risk_data = all_data.get("risks", {})
        overall_risk = risk_data.get("overall_risk", {})
        if overall_risk.get("level") == "높음":
            insights.append("⚠️ 위험도가 높아 관리 강화가 필요합니다.")
        
        # 기회 기반 인사이트
        opportunities = all_data.get("opportunities", {})
        if opportunities.get("prioritized"):
            insights.append("💡 다양한 비즈니스 기회가 확인되어 전략적 접근이 필요합니다.")
        
        if not insights:
            insights.append("📊 현재 안정적인 거래 관계를 유지하고 있습니다.")
        
        return insights
    
    async def _format_analysis_response(self, results: Dict[str, Any], analysis_type: str, client_id: Optional[str]) -> str:
        """분석 결과 응답 포맷팅"""
        try:
            data = results["data"]
            response = f"📊 {self.analysis_types.get(analysis_type, '분석')} 결과\n"
            response += f"고객: {client_id or '전체 고객'}\n\n"
            
            if analysis_type == "profile":
                if client_id:
                    response += f"• 고객명: {data.get('name', 'N/A')}\n"
                    response += f"• 업종: {data.get('industry', 'N/A')}\n"
                    response += f"• 등록일: {data.get('registration_date', 'N/A')}\n"
                    response += f"• 마지막 거래: {data.get('last_transaction', 'N/A')}\n"
                    response += f"• 상태: {data.get('status', 'N/A')}\n"
                else:
                    response += f"• 전체 고객 수: {data.get('total_clients', 0)}명\n"
                    response += f"• 활성 고객: {data.get('active_clients', 0)}명\n"
                    response += f"• 이번 달 신규: {data.get('new_clients_this_month', 0)}명\n"
            
            elif analysis_type == "sales":
                response += f"• 총 매출: {data.get('total_sales', 0):,}원\n"
                response += f"• 평균 매출: {data.get('average_sales', 0):,}원\n"
                response += f"• 거래 건수: {data.get('transaction_count', 0)}건\n"
                response += f"• 성장률: {data.get('growth_rate', 0):.1f}%\n"
            
            elif analysis_type == "risk":
                overall_risk = data.get('overall_risk', {})
                response += f"• 종합 위험도: {overall_risk.get('level', 'N/A')}\n"
                recommendations = data.get('recommendations', [])
                if recommendations:
                    response += "\n🔍 권고사항:\n"
                    for i, rec in enumerate(recommendations, 1):
                        response += f"{i}. {rec}\n"
            
            elif analysis_type == "opportunity":
                prioritized = data.get('prioritized', [])
                if prioritized:
                    response += "🎯 주요 기회:\n"
                    for i, opp in enumerate(prioritized[:3], 1):
                        item = opp.get('item', {})
                        response += f"{i}. {opp.get('category', 'N/A')}: "
                        response += f"{item.get('product', item.get('opportunity', item.get('action', 'N/A')))}\n"
                
                action_items = data.get('action_items', [])
                if action_items:
                    response += "\n📋 실행 과제:\n"
                    for action in action_items:
                        response += f"• {action}\n"
            
            else:  # comprehensive
                if 'insights' in data:
                    response += "💡 주요 인사이트:\n"
                    for insight in data['insights']:
                        response += f"• {insight}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"응답 포맷팅 실패: {str(e)}")
            return f"분석 결과 포맷팅 중 오류가 발생했습니다: {str(e)}"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Agent 상태 정보"""
        return {
            "agent_name": "client_agent",
            "database_available": self.database_service.is_available(),
            "supported_analysis_types": list(self.analysis_types.keys()),
            "available_metrics": self.available_metrics,
            "features": ["profile_analysis", "sales_analysis", "risk_assessment", "opportunity_identification"]
        } 