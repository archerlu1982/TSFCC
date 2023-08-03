#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/timer.h>
#include <linux/hrtimer.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>
#include <net/sch_generic.h>
#include "datapath.h"
#include "vport-netdev.h"
#include <linux/fs.h>
#include <linux/file.h>
#include <linux/fs_struct.h>
#include <linux/fdtable.h>

#define TARGET_INTERVAL_NS 100000 // 目标间隔时间为 100 微秒
static struct hrtimer my_hrtimer;
// bool flag = false;
// int i = 0;
int l = 20;//100 * 20%
void cleanup_test_queue_length(void);
struct dict_port_count {
    char name[32];
    int state;
    int count;
};

struct dict {
    struct dict_port_count items[100];
    int size;
};

static void dict_add(struct dict *d, const char *name, int state, int count) {
    struct dict_port_count *item;
    if (d->size >= 100) {
        printk("Error: Dictionary is full!\n");
        return;
    }
    item = &d->items[d->size++];
    strncpy(item->name, name, sizeof(item->name));
    // VLOG_INFO("%s",item->key);
    item->state = state;
    item->count = count;
}

static struct dict_port_count *dict_get(struct dict *d, const char *name) {
    int i;
    for (i = 0; i < d->size; i++) {
        if (strcmp(d->items[i].name, name) == 0) {
            return &d->items[i];
        }
    }
    return NULL;
}
struct dict d = {0};

enum hrtimer_restart  print_message(struct hrtimer *timer)
{
    struct net_device *dev;
    char name[32];
    struct dict_port_count *item;
    struct vport *vport;
    struct datapath *dp;
    uint32_t qlen;

    //遍历所有网络设备
    for_each_netdev(&init_net, dev) {
        if (strstr(dev->name, "-eth") != NULL) {
            qlen = qdisc_qlen_sum(dev->qdisc);
            vport = ovs_netdev_get_vport(dev);
            if (vport  == NULL){
                continue;
            }
            dp = vport->dp;

            strcpy(name, dev->name);   
            if(dict_get(&d, name) == NULL){
                dict_add(&d, name, 0, 0);
            }
            item = dict_get(&d, name);
            // if (strcmp(dev->name, "s1-eth14") == 0) {
            //     if(qlen >= 20){
            //         flag = true;
            //     }
            //     if(flag == true){
            //         printk("qlen_is:%u\n",qlen);
            //         i++;
            //         if(i > 10000){
            //             flag = false;
            //             i = 0;
            //         }
            //     }
            // }
            if(qlen >= l){
                if(item->state == 0){
                    //todo 发送netlink到ofproto文件
                    send_ack_userspace_packet(dp,qlen,name,true);
                    item->state = 1;
                }else{
                    //todo 发送netlink到ofproto文件
                    send_ack_userspace_packet(dp,qlen,name,true);
                }
                item->count = 0;
            }else{
                if(item->state == 1){
                    item->count++;
                }
                if(item->count == 3){
                    //todo 发送恢复netlink到ofproto文件
                    send_ack_userspace_packet(dp,qlen,name,false);
                    item->state = 0;
                    item->count = 0;
                }
            }
        } else {
            continue;
        }
    }
    /* Set the timer again for the next interval */
    hrtimer_forward_now(timer, ns_to_ktime(TARGET_INTERVAL_NS));
    return HRTIMER_RESTART;
}



int init_queue_length(void)
{
    printk(KERN_INFO "Initializing Queue Length Module\n");

    hrtimer_init(&my_hrtimer, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
    my_hrtimer.function = &print_message;

    hrtimer_start(&my_hrtimer, ns_to_ktime(TARGET_INTERVAL_NS), HRTIMER_MODE_REL);

    return 0;
}


void cleanup_queue_length(void)
{
    printk(KERN_INFO "Cleaning up Queue Length Module\n");

    /* Delete the timer */
    hrtimer_cancel(&my_hrtimer);
}

