export default async (girderRest) => {
  let folder;
  girderRest.user = (await girderRest.get('user/me')).data;
  if (!girderRest.user) {
    await girderRest.login('anonymous', 'letmein');
  }
  folder = (await girderRest.get('/folder', {
    params: {parentType: 'user',
              parentId: girderRest.user._id,
              name: 'Private'}})).data[0];
  return folder;
}
