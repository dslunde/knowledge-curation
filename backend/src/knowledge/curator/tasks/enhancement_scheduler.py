"""Enhancement Queue Scheduler for automatic processing."""

from plone import api
from knowledge.curator.workflow_scripts import (
    process_enhancement_queue,
    get_queue_statistics,
    get_enhancement_queue
)
from Products.CMFCore.utils import getToolByName
from datetime import datetime
import logging
import transaction

logger = logging.getLogger("knowledge.curator.scheduler")


class EnhancementScheduler:
    """Scheduler for automatic enhancement processing."""
    
    def __init__(self, portal):
        self.portal = portal
        
    def run_scheduled_processing(self, batch_size=20, priority_threshold=50):
        """Run scheduled enhancement processing.
        
        Args:
            batch_size: Number of items to process in one run
            priority_threshold: Minimum priority to process
        """
        logger.info("Starting scheduled enhancement processing")
        
        try:
            # Get queue statistics
            stats = get_queue_statistics()
            logger.info(f"Queue contains {stats['total']} items, "
                       f"{stats['knowledge_items']} are Knowledge Items")
            
            if stats['total'] == 0:
                logger.info("Enhancement queue is empty")
                return
            
            # Process Knowledge Items first
            knowledge_items_processed = 0
            knowledge_queue = [
                item for item in get_enhancement_queue()
                if item['portal_type'] == 'KnowledgeItem' and 
                   item.get('priority', 0) >= priority_threshold
            ]
            
            if knowledge_queue:
                # Process up to half the batch size of Knowledge Items
                ki_batch_size = min(len(knowledge_queue), batch_size // 2)
                logger.info(f"Processing {ki_batch_size} Knowledge Items")
                
                processed = process_enhancement_queue(
                    batch_size=ki_batch_size,
                    content_type_filter='KnowledgeItem'
                )
                knowledge_items_processed = len(processed)
                
                for item in processed:
                    logger.info(f"Processed Knowledge Item: {item['title']} "
                               f"(priority: {item['priority']:.2f})")
            
            # Process remaining batch with other high-priority items
            remaining_batch = batch_size - knowledge_items_processed
            if remaining_batch > 0:
                other_items = [
                    item for item in get_enhancement_queue()
                    if item['portal_type'] != 'KnowledgeItem' and 
                       item.get('priority', 0) >= priority_threshold
                ]
                
                if other_items:
                    logger.info(f"Processing {remaining_batch} other items")
                    processed = process_enhancement_queue(batch_size=remaining_batch)
                    
                    for item in processed:
                        logger.info(f"Processed {item['portal_type']}: "
                                   f"{item['title']} (priority: {item['priority']:.2f})")
            
            # Commit transaction
            transaction.commit()
            
            # Log summary
            new_stats = get_queue_statistics()
            logger.info(f"Enhancement processing complete. "
                       f"Queue now contains {new_stats['total']} items")
            
        except Exception as e:
            logger.error(f"Error in scheduled enhancement processing: {str(e)}")
            transaction.abort()
            raise
    
    def cleanup_stale_entries(self, max_attempts=5, stale_days=7):
        """Clean up stale or repeatedly failed queue entries."""
        logger.info("Starting cleanup of stale enhancement queue entries")
        
        try:
            from zope.annotation.interfaces import IAnnotations
            annotations = IAnnotations(self.portal)
            queue = annotations.get('knowledge.curator.enhancement_queue', {})
            
            removed = []
            now = datetime.now()
            
            for uid, entry in list(queue.items()):
                # Remove entries with too many attempts
                if entry.get('attempts', 0) >= max_attempts:
                    removed.append({
                        'uid': uid,
                        'title': entry.get('title', 'Unknown'),
                        'reason': f"Max attempts ({max_attempts}) exceeded"
                    })
                    del queue[uid]
                    continue
                
                # Remove stale entries
                queued_at = entry.get('queued_at')
                if queued_at:
                    try:
                        queued_date = datetime.fromisoformat(queued_at)
                        age_days = (now - queued_date).days
                        if age_days > stale_days:
                            removed.append({
                                'uid': uid,
                                'title': entry.get('title', 'Unknown'),
                                'reason': f"Stale entry ({age_days} days old)"
                            })
                            del queue[uid]
                    except Exception:
                        pass
                
                # Verify object still exists
                try:
                    obj = api.content.get(UID=uid)
                    if not obj:
                        removed.append({
                            'uid': uid,
                            'title': entry.get('title', 'Unknown'),
                            'reason': "Object no longer exists"
                        })
                        del queue[uid]
                except Exception:
                    pass
            
            if removed:
                logger.info(f"Removed {len(removed)} stale entries from enhancement queue")
                for item in removed:
                    logger.debug(f"Removed {item['title']}: {item['reason']}")
                
                transaction.commit()
            
            return removed
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
            transaction.abort()
            raise
    
    def prioritize_recent_knowledge_items(self, hours=24):
        """Boost priority of recently created Knowledge Items."""
        logger.info(f"Boosting priority of Knowledge Items created in last {hours} hours")
        
        try:
            catalog = getToolByName(self.portal, 'portal_catalog')
            
            # Find recent Knowledge Items
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(hours=hours)
            
            brains = catalog(
                portal_type='KnowledgeItem',
                created={'query': cutoff, 'range': 'min'}
            )
            
            boosted = 0
            for brain in brains:
                obj = brain.getObject()
                
                # Check if already in queue
                from zope.annotation.interfaces import IAnnotations
                annotations = IAnnotations(self.portal)
                queue = annotations.get('knowledge.curator.enhancement_queue', {})
                
                if obj.UID() in queue:
                    # Boost existing priority
                    old_priority = queue[obj.UID()].get('priority', 0)
                    new_priority = old_priority * 1.5
                    queue[obj.UID()]['priority'] = new_priority
                    boosted += 1
                    logger.debug(f"Boosted {obj.Title()} priority: "
                                f"{old_priority:.2f} -> {new_priority:.2f}")
                else:
                    # Add to queue with high priority
                    from knowledge.curator.workflow_scripts import queue_for_enhancement
                    queue_for_enhancement(obj, priority_override=150)
                    boosted += 1
                    logger.debug(f"Added {obj.Title()} to queue with high priority")
            
            if boosted:
                logger.info(f"Boosted priority for {boosted} recent Knowledge Items")
                transaction.commit()
            
            return boosted
            
        except Exception as e:
            logger.error(f"Error boosting priorities: {str(e)}")
            transaction.abort()
            raise


def run_enhancement_scheduler(context):
    """Entry point for cron/clock server to run enhancement scheduler."""
    portal = api.portal.get()
    scheduler = EnhancementScheduler(portal)
    
    # Run the scheduled processing
    scheduler.run_scheduled_processing(batch_size=20, priority_threshold=40)
    
    # Clean up stale entries every run
    scheduler.cleanup_stale_entries()
    
    # Boost recent Knowledge Items every 4 hours
    from datetime import datetime
    if datetime.now().hour % 4 == 0:
        scheduler.prioritize_recent_knowledge_items(hours=24)