"""Trade Executor - Handles trade execution with human-in-the-loop approval.

Implements the human approval workflow for trade execution,
allowing manual override and feedback before orders are placed.
"""

from typing import Optional, Dict, Callable
from datetime import datetime
import uuid

from .state import TraderState, OrderStatus


class TradeExecutor:
    """
    Trade executor with human-in-the-loop approval workflow.
    
    The executor prepares orders for execution but requires human
    approval before any actual trades are placed.
    """

    def __init__(
        self,
        require_approval: bool = True,
        auto_approve_threshold: float = 0.85,
        approval_callback: Optional[Callable] = None,
    ):
        """
        Initialize the trade executor.
        
        Args:
            require_approval: Whether to require human approval for trades
            auto_approve_threshold: Score threshold for auto-approval (if enabled)
            approval_callback: Optional callback for approval workflow
        """
        self.require_approval = require_approval
        self.auto_approve_threshold = auto_approve_threshold
        self.approval_callback = approval_callback

    def prepare_order(self, state: TraderState) -> dict:
        """
        Prepare trade order for execution.
        
        Creates order details and determines if human approval is required.
        """
        trade_decision = state.get("trade_decision", {})
        market_data = state.get("market_data", {})
        current_score = state.get("current_score", {})
        available_capital = state.get("available_capital", 0)
        
        current_price = market_data.get("current_price", 0)
        action = trade_decision.get("action", "HOLD")
        
        # Don't create order for HOLD
        if action == "HOLD":
            return {
                "pending_orders": [],
                "requires_human_approval": False,
                "execution_status": "NO_ACTION",
            }
        
        # Calculate order details
        quantity_percent = trade_decision.get("quantity_percent", 0)
        position_value = available_capital * quantity_percent
        quantity = int(position_value / current_price) if current_price > 0 else 0
        
        # Calculate stop loss and take profit prices
        stop_loss_percent = trade_decision.get("stop_loss_percent", 5) / 100
        take_profit_percent = trade_decision.get("take_profit_percent", 10) / 100
        
        if action == "BUY":
            stop_loss_price = current_price * (1 - stop_loss_percent)
            take_profit_price = current_price * (1 + take_profit_percent)
        else:  # SELL
            stop_loss_price = current_price * (1 + stop_loss_percent)
            take_profit_price = current_price * (1 - take_profit_percent)
        
        # Create order
        order = {
            "order_id": str(uuid.uuid4())[:8],
            "ticker": state["ticker"],
            "side": action,
            "order_type": trade_decision.get("order_type", "MARKET"),
            "quantity": quantity,
            "limit_price": trade_decision.get("limit_price"),
            "estimated_value": position_value,
            "current_price": current_price,
            "stop_loss_price": round(stop_loss_price, 2),
            "take_profit_price": round(take_profit_price, 2),
            "status": OrderStatus.PENDING.value,
            "timestamp": datetime.now().isoformat(),
            "reasoning": trade_decision.get("reasoning", ""),
            "confidence": trade_decision.get("confidence", 0),
            "entry_timing": trade_decision.get("entry_timing", "IMMEDIATE"),
            "risk_reward_ratio": trade_decision.get("risk_reward_ratio", 1.0),
        }
        
        # Determine if human approval is required
        overall_score = current_score.get("overall_score", 0)
        approval_recommendation = current_score.get("approval_recommendation", "REVISE")
        
        requires_approval = self.require_approval
        
        # Auto-approve only if score is very high and recommended
        if (
            not self.require_approval or
            (overall_score >= self.auto_approve_threshold and 
             approval_recommendation == "APPROVE")
        ):
            requires_approval = False
            order["auto_approved"] = True
            order["auto_approval_reason"] = f"Score {overall_score:.2f} >= {self.auto_approve_threshold}"
        
        return {
            "pending_orders": [order],
            "requires_human_approval": requires_approval,
            "execution_status": "PENDING_APPROVAL" if requires_approval else "READY_TO_EXECUTE",
        }

    def request_human_approval(self, state: TraderState) -> dict:
        """
        Request human approval for pending orders.
        
        This node waits for human input before proceeding.
        In a real system, this would trigger a notification and wait.
        """
        pending_orders = state.get("pending_orders", [])
        
        if not pending_orders:
            return {
                "human_approved": None,
                "execution_status": "NO_ORDERS",
            }
        
        order = pending_orders[0]
        
        # Build approval request
        approval_request = {
            "order_summary": {
                "ticker": order.get("ticker"),
                "action": order.get("side"),
                "quantity": order.get("quantity"),
                "estimated_value": f"${order.get('estimated_value', 0):,.2f}",
                "current_price": f"${order.get('current_price', 0):.2f}",
                "stop_loss": f"${order.get('stop_loss_price', 0):.2f}",
                "take_profit": f"${order.get('take_profit_price', 0):.2f}",
            },
            "confidence": order.get("confidence", 0),
            "reasoning": order.get("reasoning", ""),
            "risk_score": state.get("current_score", {}).get("risk_score", 0),
            "approval_recommendation": state.get("current_score", {}).get("approval_recommendation", "REVISE"),
        }
        
        # If callback is provided, use it
        if self.approval_callback:
            approved, feedback = self.approval_callback(approval_request)
            return {
                "human_approved": approved,
                "human_feedback": feedback,
                "execution_status": "APPROVED" if approved else "REJECTED",
            }
        
        # Default: return pending state for manual approval
        return {
            "approval_request": approval_request,
            "human_approved": None,  # Will be set by human
            "execution_status": "AWAITING_HUMAN_APPROVAL",
        }

    def execute_order(self, state: TraderState) -> dict:
        """
        Execute approved orders.
        
        In a real system, this would connect to a broker API.
        Here we simulate execution for demonstration.
        """
        pending_orders = state.get("pending_orders", [])
        human_approved = state.get("human_approved")
        requires_approval = state.get("requires_human_approval", True)
        
        if not pending_orders:
            return {
                "executed_orders": [],
                "execution_status": "NO_ORDERS",
            }
        
        # Check approval status
        if requires_approval and not human_approved:
            # Update order status to rejected
            for order in pending_orders:
                order["status"] = OrderStatus.REJECTED.value
                order["rejection_reason"] = state.get("human_feedback", "Not approved")
            
            return {
                "pending_orders": [],
                "executed_orders": [],
                "execution_status": "REJECTED",
            }
        
        # Execute orders (simulation)
        executed_orders = []
        for order in pending_orders:
            executed_order = order.copy()
            executed_order["status"] = OrderStatus.EXECUTED.value
            executed_order["execution_time"] = datetime.now().isoformat()
            executed_order["execution_price"] = order.get("current_price")  # Simulated fill at current price
            executed_order["filled_quantity"] = order.get("quantity")
            executed_orders.append(executed_order)
        
        return {
            "pending_orders": [],
            "executed_orders": state.get("executed_orders", []) + executed_orders,
            "execution_status": "EXECUTED",
        }

    def __call__(self, state: TraderState) -> dict:
        """Make executor callable for LangGraph - prepares order."""
        return self.prepare_order(state)


def create_cli_approval_callback():
    """
    Create a CLI-based approval callback for human-in-the-loop.
    
    Returns:
        Callable that prompts user for approval via CLI
    """
    def cli_approval(request: dict) -> tuple:
        print("\n" + "=" * 60)
        print("  🚨 TRADE APPROVAL REQUIRED")
        print("=" * 60)
        
        summary = request.get("order_summary", {})
        print(f"\n  Ticker:      {summary.get('ticker', 'N/A')}")
        print(f"  Action:      {summary.get('action', 'N/A')}")
        print(f"  Quantity:    {summary.get('quantity', 0)} shares")
        print(f"  Value:       {summary.get('estimated_value', 'N/A')}")
        print(f"  Price:       {summary.get('current_price', 'N/A')}")
        print(f"  Stop Loss:   {summary.get('stop_loss', 'N/A')}")
        print(f"  Take Profit: {summary.get('take_profit', 'N/A')}")
        print(f"\n  Confidence:  {request.get('confidence', 0):.1%}")
        print(f"  Risk Score:  {request.get('risk_score', 0):.2f}")
        print(f"  Recommendation: {request.get('approval_recommendation', 'N/A')}")
        print(f"\n  Reasoning: {request.get('reasoning', 'N/A')[:200]}...")
        
        print("\n" + "-" * 60)
        
        while True:
            response = input("  Approve this trade? [y/n/feedback]: ").strip().lower()
            
            if response == 'y':
                return True, "Approved by user"
            elif response == 'n':
                feedback = input("  Rejection reason (optional): ").strip()
                return False, feedback or "Rejected by user"
            elif response:
                # Treat any other input as feedback
                return False, f"User feedback: {response}"
            else:
                print("  Please enter 'y' to approve, 'n' to reject, or provide feedback.")
    
    return cli_approval
