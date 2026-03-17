from app.models import PortalGalleryCard, PortalHomeResponse, PortalModeCard


def build_portal_home_payload() -> PortalHomeResponse:
    return PortalHomeResponse(
        headline='开启你的 Agent 模式，立即造梦',
        subheadline='用对话、结果与资产流一体化的方式组织旅行灵感、规划方案与最终交付。',
        prompt_placeholder='告诉我你的出发地、目的地、日期、预算、人数，或继续修改已有方案……',
        hero_chips=['用户自配模型', '聊天主入口', '结果联动', '资产沉淀'],
        mode_cards=[
            PortalModeCard(title='旅行灵感', subtitle='从一句话需求开始', badge='Chat', accent='azure'),
            PortalModeCard(title='Agent 模式', subtitle='自动拆解约束与计划', badge='Agent', accent='cyan'),
            PortalModeCard(title='结果生成', subtitle='预算、路线与风险联动', badge='Result', accent='violet'),
            PortalModeCard(title='资产沉淀', subtitle='最近规划与结果复用', badge='Asset', accent='rose'),
        ],
        gallery_cards=[
            PortalGalleryCard(title='周末城市微度假', subtitle='高铁两小时圈 · 轻节奏美食路线', badge='发现', size='wide', theme='azure'),
            PortalGalleryCard(title='粉色春日草坡', subtitle='适合情侣与摄影主题行程', badge='灵感', size='medium', theme='mint'),
            PortalGalleryCard(title='云上小屋', subtitle='适合节气感与治愈系目的地', badge='路线', size='medium', theme='gold'),
            PortalGalleryCard(title='萌宠亲子农场', subtitle='适合家庭互动与低龄陪伴', badge='亲子', size='tall', theme='peach'),
            PortalGalleryCard(title='夜色下的创作驻留', subtitle='适合内容创作者与城市漫游', badge='专题', size='medium', theme='slate'),
            PortalGalleryCard(title='晨雾庭院早餐', subtitle='适合慢节奏酒店度假灵感', badge='住宿', size='medium', theme='sage'),
        ],
    )
